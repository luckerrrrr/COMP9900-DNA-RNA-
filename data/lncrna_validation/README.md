# lncRNA Validation Analysis - 简化版

## ? 文件说明

- `lncrna_analysis.py` - **主要分析脚本** (一个文件包含所有功能)
- `config.json` - 配置文件
- `README.md` - 使用说明

## ? 快速使用

### 方法1: 命令行参数
```bash
cd data/lncrna_validation

python3 lncrna_analysis.py \
    --gencode ../../dataset/gencode.v44.annotation.gtf \
    --gpn-msa ../../dataset/gpn_msa_training_data.json \
    --output-dir output
```

### 方法2: 配置文件
```bash
cd data/lncrna_validation

# 编辑 config.json 中的路径
python3 lncrna_analysis.py --config config.json
```

### 方法3: Python代码
```python
import sys
sys.path.append('data/lncrna_validation')

from lncrna_analysis import lncRNAAnalyzer

analyzer = lncRNAAnalyzer(
    gencode_path="dataset/gencode.v44.annotation.gtf",
    gpn_msa_path="dataset/gpn_msa_training_data.json",
    output_dir="output"
)

results = analyzer.run_analysis(window_size=150)
```

## ? 输出文件

分析会在输出目录生成：
- `lncrna_analysis.png` - 可视化图表
- `lncrna_analysis_report.json` - 详细分析报告

## ? 依赖包

```bash
pip install matplotlib numpy
```

## ? 分析内容

1. **GENCODE GTF解析** - 提取基因区域和lncRNA信息
2. **GPN-MSA数据处理** - 解析训练窗口数据
3. **基因组交集分析** - 查找重叠区域
4. **统计报告生成** - 覆盖率和交集统计
5. **可视化图表** - 4个统计图表

## ? 功能特性

- ? 一个文件包含所有功能
- ? 支持JSON和BED格式数据
- ? 自动生成统计报告
- ? 可视化图表生成
- ? 命令行和配置文件支持
- ? 完善的错误处理

## ? 报告内容

生成的JSON报告包含：
- 总GENCODE区域数量
- lncRNA覆盖百分比
- 训练窗口统计
- 交集分析结果
- 顶级交集基因列表
- 染色体分布统计
