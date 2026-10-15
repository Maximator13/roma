import { test, type Page } from '@playwright/test'

test.skip(!!process.env.CI, 'captures are reviewed locally')

async function capture(page: Page, name: string, project: string, wait = 3500) {
  await page.waitForTimeout(wait)
  await page.screenshot({ path: `test-results/look-${name}-${project}.png` })
}

async function showEra(page: Page, era: string) {
  await page.getByRole('button', { name: new RegExp(`^${era},`) }).click()
}

test('capture the main screens', async ({ page }, testInfo) => {
  test.setTimeout(180_000)
  const project = testInfo.project.name
  await page.goto('./')
  await page.locator('.eras__button').first().waitFor()
  await capture(page, 'home', project, 6000)
  await showEra(page, 'République')
  await capture(page, 'republique', project)
  await page.keyboard.press('PageDown')
  await capture(page, 'haut-empire', project)
  await page.keyboard.press('PageDown')
  await capture(page, 'crise', project)
  await page.keyboard.press('PageDown')
  await capture(page, 'bas-empire', project)
  await page.keyboard.press('PageDown')
  await capture(page, 'orient', project)
  await page.goto('./#/evenement/bataille-de-cannes')
  await capture(page, 'cannes', project, 6000)
})
