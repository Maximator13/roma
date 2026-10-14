import { test } from '@playwright/test'

test.skip(!process.env.OG_IMAGE, 'run with OG_IMAGE=1 to regenerate public/og-image.jpg')
test.use({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 })

test('capture the social sharing image', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await page.goto('./?quality=high')
  await page.locator('.eras__button').first().waitFor()
  await page.getByRole('button', { name: /^Haut-Empire,/ }).click()
  await page.waitForTimeout(4000)
  await page.screenshot({ path: 'public/og-image.jpg', type: 'jpeg', quality: 82 })
})
