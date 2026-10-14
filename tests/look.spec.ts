import { test, type Page } from '@playwright/test'

test.skip(!!process.env.CI, 'captures are reviewed locally')

async function capture(page: Page, name: string, project: string) {
  await page.waitForTimeout(2500)
  await page.screenshot({ path: `test-results/look-${name}-${project}.png` })
}

test('capture the main screens', async ({ page }, testInfo) => {
  const project = testInfo.project.name
  await page.goto('./')
  await page.locator('.eras__button').first().waitFor()
  await capture(page, 'home', project)
  await page.getByRole('button', { name: /^République,/ }).click()
  await capture(page, 'republique', project)
  await page.goto('./#/evenement/bataille-de-cannes')
  await capture(page, 'cannes', project)
  await page.goto('./#/evenement/sac-de-constantinople-1204')
  await capture(page, 'pistes-1204', project)
})
