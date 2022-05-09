import {SideHeading, SideLink} from "../views/nav";
import m from "mithril";
import routes from "../utils/routes";


function getMenuItems() {
  return [
    m(SideHeading, 'Files'),
    m(SideLink, {iconClass: "fa-solid fa-box", href: routes.library_index}, "My libraries"),
  ]
}

export {
  getMenuItems,
}