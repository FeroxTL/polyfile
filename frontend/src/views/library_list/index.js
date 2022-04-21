import {globalLibraryData} from "../../models/library";
import m from "mithril";
import {SideNavView} from "../nav";
import {Loader} from "../../components/bootstrap/loader";
import {modal} from "../../components/bootstrap/modal";
import TopNavBarLibraryMenu from "./top_bar_library_menu";
import LibraryListView from "./library_list_view";


let LibraryListWrapperView = {
  oninit: () => (globalLibraryData.fetch()),
  view: function () {
    return m(SideNavView, {
      topNavBarComponent: TopNavBarLibraryMenu,
    }, [
      globalLibraryData.status === "done" ? m(LibraryListView) : m(Loader),
      modal.renderModal(),
    ])
  }
};


export default LibraryListWrapperView;
