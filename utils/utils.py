def norm_chrom_name(chrom: str) -> str:
    """
    将 'chr1' 或 '1' 都规范为 '1'（去掉 'chr' 前缀，保留 X/Y/M 等）
    """
    if chrom.lower().startswith("chr"):
        return chrom[3:]
    return chrom

def print_section(title: str):
    """Pretty print section titles for better console readability."""
    print("\n" + "═" * 70)
    print(f"{title:^70}")
    print("═" * 70 + "\n")
    

def parse_attr(attr, key):
    """Extract a specific key-value pair from a GTF attribute column."""
    for a in attr.split(";"):
        if key in a:
            parts = a.split('"')
            if len(parts) > 1:
                return parts[1]
    return None



def debug_log(message: str, level: str = "INFO"):
    """
    Print formatted debug messages with log level indicators.

    Args:
        message (str): Text to display in the log.
        level (str): One of ["INFO", "WARN", "ERROR", "DEBUG", "SUCCESS"].
    """
    prefix = {
        "INFO": "ℹ️ ",
        "WARN": "⚠️ ",
        "ERROR": "❌",
        "DEBUG": "🔍",
        "SUCCESS": "✅"
    }.get(level, "  ")
    print(f"{prefix} {message}")