const {chromium}=require('playwright'),assert=require('assert');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base=process.argv[2],root=process.argv[3];await page.goto(base);
 await page.locator('#new-path').fill(root+'/2026.belegdb');await page.locator('#new-year-value').fill('2026');await page.locator('#new-year').click();
 await page.getByText('Buchungsjahr 2026',{exact:true}).waitFor();await page.locator('[data-tab="archive"]').click();await page.locator('#manual-open').click();
 await page.locator('#manual-dialog').waitFor();assert((await page.locator('#manual-number').textContent()).includes('VTUER26001'));
 await page.locator('#manual-cancel').click();await page.locator('#manual-open').click();await page.locator('#manual-dialog').waitFor();
 assert((await page.locator('#manual-number').textContent()).includes('VTUER26001'));
 await page.locator('#manual-provider').fill('Split Lieferant');await page.locator('#manual-date').fill('2026-11-12');await page.locator('#manual-amount').fill('1646,23');await page.locator('#manual-original').fill('R-123');await page.locator('#manual-note').fill('Splitbuchung Test');await page.locator('#manual-save').click();
 await page.locator('#manual-dialog').waitFor({state:'hidden'});await page.locator('#history').getByText('VTUER26001',{exact:true}).waitFor();
 assert((await page.locator('#history').textContent()).includes('Manuell in WISO gebucht · Splitbuchung Test'));
 assert.equal(await page.locator('#history a').count(),0);
 await page.locator('#history-search').fill('Splitbuchung Test');assert.equal(await page.locator('#history tr').count(),1);
 await page.locator('#manual-open').click();await page.locator('#manual-dialog').waitFor();assert((await page.locator('#manual-number').textContent()).includes('VTUER26002'));
 await page.locator('#manual-provider').fill('PDF Lieferant');await page.locator('#manual-date').fill('2026-11-12');await page.locator('#manual-amount').fill('12,50');await page.locator('#manual-pdf').fill(root+'/Eingang/rechnung.pdf');await page.locator('#manual-save').click();await page.locator('#manual-dialog').waitFor({state:'hidden'});
 await page.locator('#history a').waitFor();const pdf=await page.request.get(await page.locator('#history a').getAttribute('href'));assert.equal(pdf.status(),200);assert(pdf.headers()['content-type'].includes('application/pdf'));
 assert.deepEqual(errors,[]);await browser.close();console.log('Manual UI passed: cancel, save without/with PDF, history, notes, numbering, PDF link.');
})().catch(e=>{console.error(e);process.exit(1)});
