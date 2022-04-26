function getClassList(attrs) {
  const classList = [];
  if (attrs.hasOwnProperty("class")) {
    classList.push(...attrs["class"].split(" "));
  }
  if (attrs.hasOwnProperty("classList")) {
    classList.push(...attrs["classList"])
  }
  return classList
}

export {getClassList};
