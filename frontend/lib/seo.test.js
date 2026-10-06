import assert from "node:assert/strict";
import test from "node:test";
import {
  DEFAULT_OG_IMAGE,
  SITE_NAME,
  SITE_URL,
  absoluteUrl,
  breadcrumbJsonLd,
  faqJsonLd,
  jsonLdHtml,
  pageMetadata,
} from "./seo.ts";

test("pageMetadata sets the page's own canonical, share title and url", () => {
  const m = pageMetadata({
    title: "Help & FAQ",
    description: "Answers.",
    path: "/help",
  });
  assert.equal(m.title, "Help & FAQ");
  assert.equal(m.description, "Answers.");
  assert.deepEqual(m.alternates, { canonical: "/help" });
  assert.equal(m.openGraph.url, "/help");
  assert.equal(m.openGraph.siteName, SITE_NAME);
  assert.equal(m.openGraph.type, "website");
  assert.equal(m.openGraph.title, "Help & FAQ · Resland");
  assert.equal(m.openGraph.description, "Answers.");
});

test("pageMetadata uses an absolute title as-is for sharing", () => {
  const m = pageMetadata({
    title: { absolute: "Resland: AI Resume Tailoring" },
    description: "d",
    path: "/",
  });
  assert.deepEqual(m.title, { absolute: "Resland: AI Resume Tailoring" });
  assert.equal(m.openGraph.title, "Resland: AI Resume Tailoring");
});

test("pageMetadata points at the default share card unless the page has its own", () => {
  // Next drops a parent's openGraph images once a page sets openGraph, so
  // pages without their own opengraph-image file must name one.
  const plain = pageMetadata({ title: "t", description: "d", path: "/help" });
  assert.deepEqual(plain.openGraph.images, [DEFAULT_OG_IMAGE]);

  // ...and pages with one must not, or the file is ignored.
  const own = pageMetadata({
    title: "t",
    description: "d",
    path: "/dsa/tries",
    type: "article",
    ownImage: true,
  });
  assert.equal(Object.hasOwn(own.openGraph, "images"), false);
  assert.equal(own.openGraph.type, "article");
});

test("pageMetadata leaves twitter to inherit from openGraph", () => {
  // Setting twitter.title here would bring back the bug where every page
  // shared as the home page.
  const m = pageMetadata({ title: "t", description: "d", path: "/x" });
  assert.equal(m.twitter, undefined);
});

test("absoluteUrl joins paths onto the site", () => {
  assert.equal(absoluteUrl("/"), `${SITE_URL}/`);
  assert.equal(absoluteUrl("/dsa/tries"), `${SITE_URL}/dsa/tries`);
});

test("breadcrumbJsonLd numbers the trail from 1 with absolute URLs", () => {
  assert.deepEqual(
    breadcrumbJsonLd([
      { name: "Resland", path: "/" },
      { name: "DSA Study Center", path: "/dsa" },
      { name: "Tries", path: "/dsa/tries" },
    ]),
    {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: [
        { "@type": "ListItem", position: 1, name: "Resland", item: `${SITE_URL}/` },
        { "@type": "ListItem", position: 2, name: "DSA Study Center", item: `${SITE_URL}/dsa` },
        { "@type": "ListItem", position: 3, name: "Tries", item: `${SITE_URL}/dsa/tries` },
      ],
    },
  );
});

test("faqJsonLd wraps each pair as a Question with an accepted Answer", () => {
  assert.deepEqual(faqJsonLd([["Q1?", "A1."], ["Q2?", "A2."]]), {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      { "@type": "Question", name: "Q1?", acceptedAnswer: { "@type": "Answer", text: "A1." } },
      { "@type": "Question", name: "Q2?", acceptedAnswer: { "@type": "Answer", text: "A2." } },
    ],
  });
});

test("jsonLdHtml escapes < so content can't close the script tag", () => {
  const html = jsonLdHtml({ name: "</script><script>alert(1)</script>" });
  assert.equal(html.includes("<"), false);
  assert.deepEqual(JSON.parse(html), { name: "</script><script>alert(1)</script>" });
});
