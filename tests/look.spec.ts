import { test } from '@playwright/test'

test('capture the home screen', async ({ page }, testInfo) => {
  await page.goto('./')
  await page.locator('.eras__button').first().waitFor()
  await page.waitForTimeout(2500)
  await page.screenshot({ path: `test-results/look-home-${testInfo.project.name}.png` })
  await page.keyboard.press('PageDown')
  await page.keyboard.press('PageDown')
  await page.waitForTimeout(1500)
  await page.screenshot({ path: `test-results/look-era-${testInfo.project.name}.png` })
  await page.goto('./?debug#/mentions-legales')
  await page.waitForTimeout(2500)
  await page.screenshot({ path: `test-results/look-page-${testInfo.project.name}.png` })
})
