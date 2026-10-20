"""Временная проверка генератора бирок без импорта fastapi-зависимостей."""
import ast
import re
from typing import Optional

SRC = "backend/src/presentation/http/routers/marking.py"
tree = ast.parse(open(SRC, encoding="utf-8").read())
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_render_label_html")
ns = {"Optional": Optional}
code = compile(ast.Module(body=[fn], type_ignores=[]), SRC, "exec")
exec(code, ns)
render = ns["_render_label_html"]

html = render(
    name="Устройство для прошивки документов 1 сверло вертик.",
    inventory_number="01142947121201600000000001",
    responsible="Иванов И.И.",
    purchase_date="12.05.2023",
    company_name="ООО «ПАО»",
    company_short="ПАО",
    logo_url="/api/marking/logos/logo_test.png",
    qr_data_url="data:image/png;base64,QUJD",
    label_width=105,
    label_height=37,
)

print("HTML len:", len(html))
print("First 400 chars:", html[:400])
# Check for literal (unsubstituted) placeholders
leftovers = re.findall(r'\{[a-z_]+\}', html)
print("Leftover placeholders:", leftovers if leftovers else "NONE - all substituted OK")
