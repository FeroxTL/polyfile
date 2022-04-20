function parsePath(url) {
  const regex = /\/files([\/\w\-\. ]*)[^#?\s]*/;
  let search = regex.exec(url);

  if (search !== null && search.length === 2) {
    return search[1];
  }
  return "";
}


function splitPathStr(path) {
  return path.split("/").filter((elem) => (elem));
}


export {parsePath, splitPathStr};
