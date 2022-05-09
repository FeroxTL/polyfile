import {m} from "mithril";

const Loader = {
  view: () => (
    m("div.spinner-border[role=status]", m("span.visually-hidden", "Loading..."))
  )
};

export {Loader};