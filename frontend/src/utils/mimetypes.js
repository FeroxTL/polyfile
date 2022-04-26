import m from "mithril";
import {getClassList} from "./parse";


const IconClasses = {
  default: "fa-solid fa-file-circle-question",
  directory: "fa-solid fa-folder",
  "image": "fa-solid fa-image",

  getClass: function(mimeTypes=[]) {
    for (let type of mimeTypes) {
      if (this.hasOwnProperty(type)) {
        return this[type];
      }
    }
    return null;
  }
};


const MimeIcon = {
  view: function(vnode) {
    const {mimeType = "", iconClass = null} = vnode.attrs;

    if (iconClass) {
      return m("i", {class: [iconClass, ...getClassList(vnode.attrs)].join(" ")})
    }

    const mimeTypes = [mimeType];
    if (mimeType.indexOf("/") !== -1) {
      mimeTypes.push(mimeType.split("/", 1)[0])
    }
    let mimeClass = IconClasses.getClass(mimeTypes) || IconClasses.default;

    return m("i", {class: [mimeClass, ...getClassList(vnode.attrs)].join(" ")})
  }
};


export {MimeIcon, IconClasses};