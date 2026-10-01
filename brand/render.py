import pathlib
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1200, "height": 600})
    pg.goto((here / "logo.html").as_uri())
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(here / "exo_ac_logo.png"))
    pg.locator("#mark").screenshot(path=str(here / "exo_ac_icon.png"), omit_background=True)
    b.close()
