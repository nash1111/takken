export async function onRequest(context) {
  const url = new URL(context.request.url);
  const match = url.pathname.match(/^\/questions\/takken_\d+_(.+?)\/?$/);

  if (match) {
    const canonicalPath = `/questions/${match[1]}/`;
    const target = new URL(canonicalPath, url.origin);
    target.search = url.search;
    return Response.redirect(target.toString(), 301);
  }

  return context.env.ASSETS.fetch(context.request);
}
