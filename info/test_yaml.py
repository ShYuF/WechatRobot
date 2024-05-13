import yaml
import os
import re

file = open(r"ddlkey.yaml", "r", encoding="utf-8")
file_data = file.read()
file.close()

data = yaml.safe_load(file_data)

q = "ddl\n2022012068\ng"
mat = re.match("ddl\n(\d{10})(\n(.+))?", q)
if ("p" + mat.group(1) in data.keys()):
    print (data["p" + mat.group(1)])
print(mat.group(3))
