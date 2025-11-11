import re
from pathlib import Path
from typing import Dict, Optional, List
import numpy as np

# 依赖你项目里的 norm_chrom_name（已在 preprocess 中存在）
try:
    from utils.utils import norm_chrom_name
except Exception:
    def norm_chrom_name(chrom: str) -> str:
        if chrom is None:
            return ""
        s = str(chrom)
        return s[3:] if s.lower().startswith("chr") else s

class WigFixLoader:
    """
    极简版 WIG fixedStep 解析器（memory-light）。
    - load(wig_path)：解析文件，保存每个 fixedStep block（按染色体分组）。
      block 格式：{"start": int, "step": int, "values": List[float]}
    - get_window_mean(chrom, start, end)：返回窗口内所有可用值的平均值（float），
      若窗口内没有任何值则返回 None。
    说明：
    - 使用 1-based 坐标（和 GTF/FASTA 保持一致）
    - 对于 value 行，支持小数点写成逗号的容错（"0,253" -> 0.253）
    """
    FIXEDSTEP_RE = re.compile(
        r"fixedStep\s+chrom=(?P<chrom>\S+)\s+start=(?P<start>\d+)(?:\s+step=(?P<step>\d+))?",
        re.I
    )

    def __init__(self):
        self.blocks_by_chrom: Dict[str, List[Dict]] = {}

    def load(self, wig_path: str, verbose: bool = False):
        p = Path(wig_path)
        if not p.exists():
            raise FileNotFoundError(f"WIG file not found: {wig_path}")

        self.blocks_by_chrom.clear()
        cur_chrom = None
        cur_start = None
        cur_step = 1
        cur_values: List[float] = []
        lines = 0
        blocks = 0
        bad_values = 0
        bad_headers = 0

        with open(p, 'r') as fh:
            for raw in fh:
                lines += 1
                line = raw.strip()
                if not line:
                    continue
                if line.lower().startswith("fixedstep"):
                    # flush previous block
                    if cur_chrom is not None and cur_values:
                        self.blocks_by_chrom.setdefault(cur_chrom, []).append({
                            "start": cur_start,
                            "step": cur_step,
                            "values": cur_values
                        })
                        blocks += 1
                    # parse header
                    m = self.FIXEDSTEP_RE.match(line)
                    if not m:
                        bad_headers += 1
                        cur_chrom = None
                        cur_values = []
                        continue
                    raw_chrom = m.group("chrom")
                    cur_chrom = norm_chrom_name(raw_chrom)
                    cur_start = int(m.group("start"))
                    cur_step = int(m.group("step")) if m.group("step") else 1
                    cur_values = []
                    continue

                # numeric value line within a block
                if cur_chrom is None:
                    continue
                try:
                    val = float(line.replace(",", "."))
                except Exception:
                    bad_values += 1
                    continue
                cur_values.append(val)

        # flush last block
        if cur_chrom is not None and cur_values:
            self.blocks_by_chrom.setdefault(cur_chrom, []).append({
                "start": cur_start,
                "step": cur_step,
                "values": cur_values
            })
            blocks += 1

        if verbose:
            print(f"[WIG] parsed lines={lines}, blocks={blocks}, bad_values={bad_values}, bad_headers={bad_headers}")
            for c, bl in self.blocks_by_chrom.items():
                print(f"  chrom {c}: {len(bl)} blocks")

    def get_window_mean(self, chrom: str, start: int, end: int) -> Optional[float]:
        """
        计算并返回窗口 [start, end]（1-based inclusive）内的 phastCons 平均值或 None。
        直接按 block 重叠区间累加求和／计数（不构建整窗数组）。
        """
        key = norm_chrom_name(chrom)
        blocks = self.blocks_by_chrom.get(key)
        if not blocks:
            return None

        if end < start:
            return None

        total = 0.0
        count = 0

        for blk in blocks:
            blk_start = int(blk["start"])   # 1-based
            blk_step = int(blk["step"])
            vals = blk["values"]
            n_vals = len(vals)
            # block 的末端位置（1-based）
            blk_end = blk_start + (n_vals - 1) * blk_step

            # 计算 overlap [ov_s, ov_e]（1-based）
            ov_s = max(start, blk_start)
            ov_e = min(end, blk_end)
            if ov_s > ov_e:
                continue

            # block 内对应索引 j0..j1
            j0 = (ov_s - blk_start) // blk_step
            j1 = (ov_e - blk_start) // blk_step
            if j0 < 0:
                j0 = 0
            if j1 >= n_vals:
                j1 = n_vals - 1
            if j0 > j1:
                continue

            # 累加片段
            # 直接用 python 内建 sum 对 slice 更快
            slice_vals = vals[j0:j1 + 1]
            # 小心 slice 里若含 None 应跳过（但一般不会）
            for v in slice_vals:
                if v is None:
                    continue
                total += float(v)
                count += 1

        if count == 0:
            return None
        return total / count
