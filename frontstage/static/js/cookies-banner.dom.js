async function cookiesBanner() {
  const cookiesBanner = [...document.querySelectorAll('.cookies-banner')];

  if (cookiesBanner.length) {
    const CookiesBanner = (await import('./cookies-banner.js')).default;
    cookiesBanner.forEach(banner => {
      new CookiesBanner(banner);
    });
  }
}

cookiesBanner();
