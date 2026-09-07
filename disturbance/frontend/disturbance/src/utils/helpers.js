import $ from "jquery";

function unwrapErrorDetail(input) {
  //Error unwrap for DRF errors

  if (typeof input !== "string") return input;
  let t = input.trim();
  // If the whole string is bracketed once, strip it: "[...]" -> "..."
  if (t.startsWith("[") && t.endsWith("]")) {
    t = t.slice(1, -1).trim();
  }

  // If still quoted, strip quotes
  if (
    (t.startsWith('"') && t.endsWith('"')) ||
    (t.startsWith("'") && t.endsWith("'"))
  ) {
    t = t.slice(1, -1).trim();
  }

  // single or double quotes
  const m =
    t.match(/ErrorDetail\s*\(\s*string\s*=\s*'([^']*)'/) ||
    t.match(/ErrorDetail\s*\(\s*string\s*=\s*"([^"]*)"/);

  if (m) return m[1];

  // If it's a simple one-item list in string form
  const bracketMsg =
    t.match(/^\[\s*'([^']*)'\s*\]$/) || t.match(/^\[\s*"([^"]*)"\s*\]$/);

  if (bracketMsg) return bracketMsg[1];

  return input;
}

/*

*/
function extractDrfMessages(data) {
  if (data == null || data === "") return [];

  // 1. If it's a string, try JSON parsing it
  if (typeof data === "string") {
    const trimmed = data.trim();
    if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
      try {
        return extractDrfMessages(JSON.parse(trimmed));
      } catch {
        // Plain text string
      }
    }

    return [data];
  }

  // 2. If it's an array
  if (Array.isArray(data)) {
    return data.flatMap((item) => extractDrfMessages(item));
  }

  // 3. If it's an object
  if (typeof data === "object") {
    if (data.non_field_errors) {
      return extractDrfMessages(data.non_field_errors);
    }
    if (data.detail) {
      return extractDrfMessages(data.detail);
    }
    if (data.message) {
      return extractDrfMessages(data.message);
    }
    if (data.error) {
      return extractDrfMessages(data.error);
    }

    // Field-level errors: { field: ["Error message"] }
    const messages = [];
    for (const [key, value] of Object.entries(data)) {
      const fieldErrors = extractDrfMessages(value);
      const fieldName = key.replace(/_/g, " ");
      const capitalized =
        fieldName.charAt(0).toUpperCase() + fieldName.slice(1);

      fieldErrors.forEach((msg) => {
        messages.push(`${capitalized}: ${msg}`);
      });
    }
    return messages;
  }

  return [String(data)];
}

export async function parseFetchError(response) {
  if (!response) {
    return "Network error. Please check your connection.";
  }

  // Common wrapper objects (e.g. if an Error object with an attached response was passed)
  const res = response.response || response;
  const status = res.status;

  console.log(res)

  if (status === 404) return "The requested resource was not found.";
  if (status >= 500) return "A server error occurred. Please try again later.";

  let data;

  // 1. If it's a Fetch Response object
  if (typeof res.json === "function" || res instanceof Response) {
    try {
      // Try to read directly
      data = await res.json();
    } catch {
      try {
        // If not JSON, try text
        data = await res.text();
      } catch {
        // If stream was already read, try reading from properties if your wrapper cached it
        data = res._bodyInit || res.data || res.body;
      }
    }
  } else {
    // 2. If it's already a parsed object / data payload
    data = res.data || res.body || res;
  }

  const messages = extractDrfMessages(data);

  if (messages.length > 0) {
    return messages.join("\n");
  }

  // Fallback if the body was completely empty
  return res.statusText || "An unexpected error occurred.";
}

export default {
  truncate(text, { length = 30, omission = "...", separator } = {}) {
    if (text == null) return "";
    const str = String(text);
    if (str.length <= length) return str;
    const end = length - omission.length;
    if (end < 1) return omission;
    let slice = str.slice(0, end);
    if (separator) {
      const sepIdx = slice.lastIndexOf(separator);
      if (sepIdx > -1) {
        slice = slice.slice(0, sepIdx);
      }
    }
    return slice + omission;
  },
  escapeAttr(value) {
    // Normalize first so objects/arrays become readable JSON not [object Object]
    let str;
    if (value == null) {
      str = "";
    } else if (typeof value === "string") {
      str = value;
    } else if (typeof value === "number" || typeof value === "boolean") {
      str = String(value);
    } else {
      try {
        str = JSON.stringify(value);
      } catch {
        str = String(value);
      }
    }
    return str
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  },
  apiError: function (resp) {
    var error_str;
    if (resp.status === 400) {
      try {
        let obj = JSON.parse(resp.responseText);
        error_str = obj.non_field_errors[0].replace(/[[\]"]/g, "");
      } catch (e) {
        console.log(e);
        error_str = resp.responseText.replace(/[[\]"]/g, "");
      }
    } else if (resp.status === 404) {
      error_str = "The resource you are looking for does not exist.";
    } else {
      error_str = resp.responseText.replace(/[[\]"]/g, "");
    }
    return error_str;
  },
  apiVueResourceError: async function (resp) {
    let body;
    try {
      body = await resp.clone().json();
    } catch {
      try {
        body = await resp.text();
      } catch {
        body = "";
      }
    }

    let error_str = "";
    let text;

    if (resp.status === 400) {
      if (Array.isArray(body)) {
        text = body[0];
      } else if (typeof body === "object" && body !== null) {
        text = body;
      } else {
        text = body;
      }

      if (typeof text === "object" && text !== null) {
        if (Object.prototype.hasOwnProperty.call(text, "non_field_errors")) {
          const first = text.non_field_errors && text.non_field_errors[0];
          let cleaned = unwrapErrorDetail(
            typeof first === "string" ? first : String(first || ""),
          );
          cleaned = cleaned.replace(/[[\]"]/g, "").replace(/^'"['"]$/, "$1");
          error_str = cleaned;
        } else {
          error_str = JSON.stringify(text);
        }
      } else if (typeof text === "string") {
        let cleaned = unwrapErrorDetail(text);
        cleaned = cleaned.replace(/[[\]"]/g, "").replace(/^'"['"]$/, "$1");
        error_str = cleaned;
      }
    } else if (resp.status === 404) {
      error_str = "The resource you are looking for does not exist.";
    }
    console.log(error_str);
    return error_str;
  },

  /**
   * Universal error parser for our vue 3 / fetch setup.
   * I am leaving the old `apiError` and `apiVueResourceError` functions in place for now for backward compatibility.
   */
  parseApiError: async function (response) {
    // Handle network drops or non-response errors
    if (!response) {
      return "Network error. Please check your connection.";
    }

    const status = response.status;

    // Standard status code fallbacks
    if (status === 404) return "The requested resource was not found.";
    if (status === 401) return "Your session has expired. Please log in again.";
    if (status === 403)
      return "You do not have permission to perform this action.";
    if (status >= 500)
      return "A server error occurred. Please try again later.";

    // Extract body
    let data;
    try {
      // Works with Fetch Response
      if (typeof response.clone === "function") {
        data = await response.clone().json();
      } else if (typeof response.json === "function") {
        data = await response.json();
      } else if (response.data) {
        // Axios response
        data = response.data;
      } else if (response.responseText) {
        // XMLHttpRequest
        data = JSON.parse(response.responseText);
      }
    } catch {
      // If JSON parsing fails, fallback to text
      try {
        data =
          typeof response.text === "function"
            ? await response.text()
            : response.statusText;
      } catch {
        data = "An unexpected error occurred.";
      }
    }

    const errors = extractDrfMessages(data);
    return errors.length > 0
      ? errors.join("\n")
      : "An unexpected error occurred.";
  },

  goBack: function (vm) {
    vm.$router.go(window.history.back());
  },
  copyObject: function (obj) {
    return JSON.parse(JSON.stringify(obj));
  },
  getCookie: function (name) {
    var value = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1).trim() === name + "=") {
          value = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return value;
  },
  namePopover: function ($, vmDataTable) {
    vmDataTable.on("mouseover", ".name_popover", function () {
      $(this).popover("show");
      $(this).on("mouseout", function () {
        $(this).popover("hide");
      });
    });
  },
  add_endpoint_join: function (api_string, addition) {
    // assumes api_string has trailing forward slash "/" character required for POST
    return api_string + addition;
  },
  add_endpoint_json: function (string, addition) {
    var res = string.split(".json");
    return res[0] + "/" + addition + ".json";
  },
  dtPopover(value, truncate_length = 30, trigger = "hover") {
    const ellipsis = "...";
    const raw = value == null ? "" : String(value);
    const truncated = this.truncate(raw, {
      length: truncate_length,
      omission: ellipsis,
      separator: " ",
    });
    let result = "<span>" + truncated + "</span>";
    if (raw.length > truncated.length) {
      result += `<a class="mx-0 ps-1 pe-0" href="javascript://"
                role="button"
                data-bs-toggle="popover"
                data-bs-trigger="${this.escapeAttr(trigger)}"
                data-bs-placement="top"
                data-bs-html="true"
                data-bs-content="${this.escapeAttr(raw)}"
            ><small>More</small></a>`;
    }
    return result;
  },
  dtPopoverCellFn: function (cell) {
    $(cell)
      .find('[data-bs-toggle="popover"]')
      .each(function () {
        new bootstrap.Popover(this);
      });
  },
  enablePopovers: function () {
    let popoverTriggerList = [].slice.call(
      document.querySelectorAll('[data-bs-toggle="popover"]'),
    );
    // eslint-disable-next-line no-unused-vars
    let popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });
  },
  guid: function () {
    function s4() {
      return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
    }
    return (
      s4() +
      s4() +
      "-" +
      s4() +
      "-" +
      s4() +
      "-" +
      s4() +
      "-" +
      s4() +
      s4() +
      s4()
    );
  },
  mimic_redirect: function (url, postData) {
    console.log("in mimic...");
    /* http.post and ajax do not allow redirect from Django View (post method),
          this function allows redirect by mimicking a form submit.

          usage:  vm.post_and_redirect(vm.application_fee_url, {'csrfmiddlewaretoken' : vm.csrf_token});
      */
    var postFormStr = "<form method='POST' action='" + url + "'>";

    for (var key in postData) {
      if (Object.prototype.hasOwnProperty.call(postData, key)) {
        postFormStr +=
          "<input type='hidden' name='" +
          key +
          "' value='" +
          postData[key] +
          "'>";
      }
    }
    postFormStr += "</form>";
    var formElement = $(postFormStr);
    $("body").append(formElement);
    $(formElement).submit();
  },
  processError: async function (err) {
    console.log(err);
    let errorText = "";
    if (err.body && err.body.non_field_errors) {
      console.log("non_field_errors");
      // When non field errors raised
      for (let i = 0; i < err.body.non_field_errors.length; i++) {
        errorText += err.body.non_field_errors[i] + "<br />";
      }
    } else if (err.body && Array.isArray(err.body)) {
      console.log("isArray");
      // When serializers.ValidationError raised
      for (let i = 0; i < err.body.length; i++) {
        errorText += err.body[i] + "<br />";
      }
    } else if (err.body) {
      console.log("else");
      // When field errors raised
      for (let field_name in err.body) {
        if (Object.prototype.hasOwnProperty.call(err.body, field_name)) {
          errorText += field_name + ":<br />";
          for (let j = 0; j < err.body[field_name].length; j++) {
            errorText += err.body[field_name][j] + "<br />";
          }
        }
      }
    }
    await swal.fire({
      title: "Error",
      text: errorText,
      icon: "error",
      customClass: {
        confirmButton: "btn btn-primary",
      },
    });
  },
  formatFetchError: function (err) {
    console.log(err);
    let errorText = "";
    if (err.non_field_errors) {
      console.log("non_field_errors");
      // When non field errors raised
      for (let i = 0; i < err.non_field_errors.length; i++) {
        errorText += err.non_field_errors[i];
      }
    } else if (Array.isArray(err)) {
      console.log("isArray");
      // When serializers.ValidationError raised
      for (let i = 0; i < err.length; i++) {
        errorText += err[i];
      }
    } else {
      console.log("else");
      // When field errors raised
      for (let field_name in err) {
        if (Object.prototype.hasOwnProperty.call(err, field_name)) {
          errorText += field_name + ":";
          for (let j = 0; j < err[field_name].length; j++) {
            errorText += err[field_name][j];
          }
        }
      }
    }
    return errorText;
  },
};
