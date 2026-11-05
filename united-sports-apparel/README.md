# United Sports Apparel: single-page site

`index.html` is the whole site: one file, no build step. Fonts come from Google Fonts. Every photo loads from the client's own Shopify CDN (unitedsportsonline.com / cdn.shopify.com).

## Refreshing the shop section

The "Shop online" grid renders from a product snapshot embedded in `index.html`
(`<script id="catalog">`). To pull the current catalog from the live store:

```
python3 tools/build_catalog.py
```

This reads `products.json` plus the frontpage, apparel and Berrien County Parks collections, then rewrites the snapshot. Staff-only Berrien County Parks items stay out of the public shop.
