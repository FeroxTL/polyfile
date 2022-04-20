import m from 'mithril';
import {getCookie} from "../utils/cookie";


let Auth = {
  logout: function() {
    return m.request({
      method: "POST",
      url: '/api/v1/auth/logout',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      }
    })
  },
};


export {
  Auth
};
