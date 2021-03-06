import m from "mithril";
import {SideNavView} from "../nav";
import {globalNodesData} from "../../models/nodes";
import {Loader} from "../../components/bootstrap/loader";
import {modal} from "../../components/bootstrap/modal";
import TopNavBarNodeMenu from "./top_navbar_node_menu";
import NodeBreadcrumbs from "./node_breadcrumbs";
import NodeListView from "./node_list_view";
import {getMenuItems} from "../../models/menu";


let NodeListWrapperView = {
  view: function (vnode) {
    return [
      m(SideNavView, {
          topNavBarComponent: TopNavBarNodeMenu,
          sideMenuItems: getMenuItems(),
        },
        globalNodesData.status === "done" ? [
          m(NodeBreadcrumbs, vnode.attrs),
          m(NodeListView, vnode.attrs),
        ] : m(Loader)
      ),
      modal.renderModal(),
    ]
  }
};


export {NodeListWrapperView};
