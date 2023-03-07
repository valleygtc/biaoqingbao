from pathlib import Path

from pyinfra.operations import files, server, systemd

filename = input("input builded tar.gz filename: ")
filepath = Path(f"../dist/{filename}").resolve()

if not filepath.is_file():
    print(f"{filepath} not exists.")
    exit()

repo_dir = "/opt/www/biaoqingbao"

files.put(
    name=f"Upload {filepath}",
    src=str(filepath),
    dest=f"{repo_dir}/{filename}",
    mode="644",
)

server.shell(
    name="Uninstall old biaoqingbao",
    commands=[". .venv/bin/activate && pip uninstall biaoqingbao -y"],
    chdir=repo_dir,
)

server.shell(
    name="Install biaoqingbao",
    commands=[f". .venv/bin/activate && pip install {filename}[deploy]"],
    chdir=repo_dir,
)

systemd.service(
    name="Restart biaoqingbao.service",
    service="biaoqingbao",
    running=True,
    restarted=True,
    enabled=True,
)

server.wait(
    name="Wait for biaoqingbao to start",
    port=5000,
)
