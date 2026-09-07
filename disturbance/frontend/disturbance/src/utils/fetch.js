export default {
  fetchUrl: async function (url, options) {
    return new Promise((resolve, reject) => {
      let f = options === undefined ? fetch(url) : fetch(url, options);
      f.then(
        async (response) => {
          let data;
          try {
            data = await response.json();
          } catch {
            try {
              data = await response.text();
            } catch {
              data = null;
            }
          }

          if (!response.ok) {
            let error =
              (data && Array.isArray(data) && data) ||
              (data && data.message) ||
              (data &&
                (data.non_field_errors ||
                  data.detail ||
                  typeof data === "object"))
                ? data
                : response.statusText;

            return reject(error);
          }
          resolve(data);
        },
        (error) => {
          console.error(`There was an error fetching from ${url}`, error);
          error = new Error(error.NETWORK_ERROR);
          reject(error);
        },
      );
    });
  },
};
