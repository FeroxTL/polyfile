import m from "mithril";
import {modal} from "./bootstrap/modal";


const NavLiItem = {
  view: function(vnode) {
    const {selector="button"} = vnode.attrs;
    return (
      m("li.nav-item", m(`${selector}.btn btn-outline-secondary mx-1`, vnode.attrs, vnode.children))
    )
  }
};


function showImageViewer({currentNode, nodeList = []} = {}) {
  const dragState = {
    zoom: 1,
    startX: 0,
    startY: 0,
    x: 0,
    y: 0,
    $img: null,
    $container: null,
    reset: function () {
      this.zoom = 1;
      this.x = 0;
      this.y = 0;
    }
  };

  function setZoom(value) {
    dragState.zoom += value;
    if (dragState.zoom < 1) {
      dragState.zoom = 1;
      //todo: very buggy; update (x, y) on every zoom out
      dragState.x = 0;
      dragState.y = 0;
    } else if (dragState.zoom > 5) {
      dragState.zoom = 5;
    }
  }

  function MouseUp(e) {
    e.preventDefault();
    window.removeEventListener('mouseup', MouseUp);
    window.removeEventListener('mousemove', MouseMove);
    dragState.$img.classList.add("gallery-image-transitions");

    const imgBoundRect = dragState.$img.getBoundingClientRect();
    const containerRect = dragState.$container.getBoundingClientRect();

    if (imgBoundRect.width >= containerRect.width) {
      if (imgBoundRect.right < containerRect.right) dragState.x += containerRect.right - imgBoundRect.right;
      if (imgBoundRect.left > containerRect.left) dragState.x -= imgBoundRect.left - containerRect.left;
    }

    if (imgBoundRect.height >= containerRect.height) {
      if (imgBoundRect.top > containerRect.top) dragState.y -= imgBoundRect.top - containerRect.top;
      if (imgBoundRect.bottom < containerRect.bottom) dragState.y += containerRect.bottom - imgBoundRect.bottom;
    }

    m.redraw();
  }

  function MouseMove(e) {
    e.preventDefault();

    const imgBoundRect = dragState.$img.getBoundingClientRect();
    const containerRect = dragState.$container.getBoundingClientRect();

    const xLocked = imgBoundRect.width <= containerRect.width;
    const yLocked = imgBoundRect.height <= containerRect.height;

    if (!xLocked) {
      dragState.x += e.pageX - dragState.startX;
      dragState.startX = e.pageX;
    }
    if (!yLocked) {
      dragState.y += e.pageY - dragState.startY;
      dragState.startY = e.pageY;
    }
    m.redraw();
  }

  const dragOptions = {
    onmousedown: (e) => {
      e.preventDefault();
      dragState.startX = e.pageX;
      dragState.startY = e.pageY;
      window.addEventListener('mouseup', MouseUp);
      window.addEventListener('mousemove', MouseMove);
      dragState.$img = e.currentTarget.getElementsByTagName('img')[0];
      dragState.$container = e.currentTarget;
      dragState.$img.classList.remove("gallery-image-transitions");
    },
    onwheel: (e) => {
      e.preventDefault();
      if (event.deltaY < 0) {
        setZoom(0.5);
      } else {
        setZoom(-0.5);
      }
    }
  };

  const ImageView = {
    getImgStyle: function () {
      const {x, y, zoom} = dragState;
      return {
        "transform": `translate3d(${x}px, ${y}px, 0px) scale3d(${zoom}, ${zoom}, 1)`
      };
    },
    getImageOptions: function (image) {
      //todo: should load thumbnail based on screen height
      return {
        src: image.downloadUrl,
        style: image === currentNode ? this.getImgStyle() : null,
      }
    },
    onSelectNext: function (node, e) {
      e.preventDefault();

      let index = nodeList.indexOf(node);
      if (index === -1) return;
      index++;
      if (index >= nodeList.length) index = 0;
      currentNode = nodeList[index];
      dragState.reset();
    },
    onSelectPrev: function (node, e) {
      e.preventDefault();

      let index = nodeList.indexOf(node);
      if (index === -1) return;
      index--;
      if (index < 0) index = nodeList.length - 1;
      currentNode = nodeList[index];
      dragState.reset();
    },

    view: function () {
      //todo: all images are loading at the same time. Should load only current image?
      const hasManyImages = nodeList.length > 0;

      return m("div.carousel slide h-100",
        hasManyImages ? [
          m("div.carousel-inner h-100", nodeList.map(image => (
            m("div.carousel-item h-100 text-center", {...dragOptions, class: image === currentNode ? "active" : null},
              m("img.h-100 gallery-image gallery-image-transitions", this.getImageOptions(image))
            )
          ))),
          m("button.carousel-control-prev h-100[type=button]", {onclick: this.onSelectPrev.bind(null, currentNode)}, [
            m("span.carousel-control-prev-icon[aria-hidden=true]"),
            m("span.visually-hidden", "Previous"),
          ]),
          m("button.carousel-control-next h-100[type=button]", {onclick: this.onSelectNext.bind(null, currentNode)}, [
            m("span.carousel-control-next-icon[aria-hidden=true]"),
            m("span.visually-hidden", "Next"),
          ]),
        ] : (
          m("div.carousel-inner h-100",
            m("div.carousel-item active h-100 text-center",
              m("img.h-100 gallery-image gallery-image-transitions", this.getImageOptions(currentNode))
            )
          )
        ),
      );
    }
  };

  const HeaderComponent = {
    closeModal: function (node, e) {
      e.preventDefault();
      modal.close();
    },
    setZoom: function (value, e) {
      e.preventDefault();
      setZoom(value);
    },
    resetZoom: function (e) {
      e.preventDefault();
      dragState.reset();
    },

    view: function () {
      let currentIndex = nodeList.indexOf(currentNode);
      if (currentIndex === -1) currentIndex = null;

      return (
        m("nav.navbar navbar-expand navbar-light bg-light",
          m('div.container-fluid', [
            currentIndex !== null && m(
              "span.navbar-text me-auto gallery-title",
              `${currentIndex + 1} / ${nodeList.length} | ${currentNode.name}`
            ),
            m("ul.navbar-nav", [
              m(NavLiItem, {onclick: this.resetZoom.bind(null)}, m("i.fa-solid fa-down-left-and-up-right-to-center")),
              m(NavLiItem, {onclick: this.setZoom.bind(null, 0.5)}, m("i.fa-solid fa-magnifying-glass-plus")),
              m(NavLiItem, {onclick: this.setZoom.bind(null, -0.5)}, m("i.fa-solid fa-magnifying-glass-minus")),
              m(NavLiItem, {selector: "a", href: currentNode.downloadUrl, target: "_blank"}, m("i.fa-solid fa-arrow-down")),
              m(NavLiItem, {onclick: this.closeModal.bind(null, currentNode)}, m("i.fa-solid fa-xmark")),
            ]),
          ])
        )
      )
    }
  };

  modal.show({
    modalDialogClass: "modal-fullscreen",
    modalBodyClass: "p-0",
    headerComponent: HeaderComponent,
  }, ImageView)
}


export default showImageViewer;
