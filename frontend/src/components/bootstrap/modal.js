import m from "mithril";


function Modal({
  buttons = null,
  title = "Modal",
  modalDialogClass = null,
  modalBodyClass = null,
  headerComponent = null,
} = {}, content = null) {
  this.modalDialog = {
    oncreate: (vnode) => {
      setTimeout(() => {
          vnode.dom.classList.add("show");
          document.body.classList.add("modal-open");
        }, 0);
    },
    onbeforeremove: function(vnode) {
      vnode.dom.classList.remove("show");
      document.body.classList.remove("modal-open");

      return new Promise(function(resolve) {
        vnode.dom.addEventListener("transitionend", resolve)
      })
    },
    view: () => {
      return (
        m("div.modal d-block fade[tabindex=-1]",
          {
            onclick: (e) => {
              if (e.target.classList.contains("modal")) this.close();
            }
          },
          m("div.modal-dialog", {class: modalDialogClass},
            m("div.modal-content", [
              headerComponent ?
                m(headerComponent) :
                m("div.modal-header", [
                  m("h5.modal-title", title),
                  m("button.btn-close[type=button]", {onclick: this.close}),
                ]),
              m("div.modal-body", {class: modalBodyClass}, content && m(content)),
              buttons && m("div.modal-footer", buttons.map((button) => m(button)))
            ])
          )
        )
      )
    }
  };

  this.modalBackdrop = {
    oncreate: (vnode) => {
      setTimeout(() => {vnode.dom.classList.add("show")}, 0);
    },
    onbeforeremove: function(vnode) {
      vnode.dom.classList.remove("show");
      return new Promise(function(resolve) {
        vnode.dom.addEventListener("transitionend", resolve)
      })
    },
    view: () => {
      return m("div.modal-backdrop fade")
    }
  };

  this.close = () => {
    this.modalDialog = null;
    this.modalBackdrop = null;
  };
}


let modal = {
  BtnCancel: {
    view: function() {
      return m("button.btn btn-secondary[type=button]", {
        onclick: () => {modal.close()},
      }, "Cancel")
    }
  },

  current_modal: null,
  show: function (options, content) {
    this.current_modal = new Modal(options, content);
  },
  close: function () {
    this.current_modal.close();
  },
  renderModal() {
    return this.current_modal && this.current_modal.modalDialog && m(this.current_modal.modalDialog);
  },
  renderBackdrop() {
    return this.current_modal && this.current_modal.modalBackdrop && m(this.current_modal.modalBackdrop);
  },
};


export {modal};
