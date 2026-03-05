import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { ogTemplate } from "../../utils/og-template";

const WIDTH = 1200;
const HEIGHT = 630;

async function loadFont(): Promise<ArrayBuffer> {
  const res = await fetch(
    "https://fonts.bunny.net/inter/files/inter-latin-700-normal.woff"
  );
  return res.arrayBuffer();
}

export async function getStaticPaths() {
  const blogPosts = await getCollection("blog", ({ data }) => !data.draft);
  const researchPosts = await getCollection("research", ({ data }) => !data.draft);
  const allPosts = [...blogPosts, ...researchPosts];

  return allPosts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }));
}

export async function GET({ props }: APIContext) {
  const { post } = props as { post: any };
  const fontData = await loadFont();

  const svg = await satori(
    ogTemplate(post.data.title, post.data.description, post.data.tags) as any,
    {
      width: WIDTH,
      height: HEIGHT,
      fonts: [
        {
          name: "Inter",
          data: fontData,
          weight: 700,
          style: "normal",
        },
      ],
    }
  );

  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: WIDTH },
  });
  const png = resvg.render().asPng();

  return new Response(png, {
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
}
