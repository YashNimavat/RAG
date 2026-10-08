"""Item 5 follow-up: SimpleDirectoryReader sorts Path objects (readers/file/base.py, `sorted(all_files)`).
Path ordering is case-insensitive on Windows and case-sensitive on POSIX. Run: python -I lab05c_sort_order.py"""
from pathlib import PurePosixPath, PureWindowsPath
names = ["Understanding_Climate_Change.pdf", "customers-100.csv", "nike_2023_annual_report.txt", "q_a.json",
         "q_a_smith.json", "q_a_smith_short.json", "wealth_retrieved_passages_from_original_memorag.csv"]
print("Windows order:", [p.name for p in sorted(PureWindowsPath("data", n) for n in names)])
print("POSIX order:  ", [p.name for p in sorted(PurePosixPath("data", n) for n in names)])
