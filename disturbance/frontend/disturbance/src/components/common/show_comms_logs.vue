<template lang="html">
  <div id="ShowComms">
    <modal
      transition="modal fade"
      :showOK="false"
      :showCancel="false"
      title="Communication logs"
      :xxlarge="true"
    >
      <div class="container-fluid">
        <datatable
          ref="datatable"
          :id="commsLogId"
          :dtOptions="commsDtOptions"
          :dtHeaders="commsDTHeaders"
        ></datatable>
      </div>
    </modal>
  </div>
</template>

<script>
import modal from "@vue-utils/bootstrap-modal.vue";
import datatable from "@vue-utils/datatable.vue";
import { v4 as uuid } from "uuid";
import { constants, helpers } from "@/utils/hooks";
export default {
  name: "Show-Comms",
  components: {
    modal,
    datatable,
  },
  props: {
    url: {
      type: String,
      required: true,
    },
  },
  data: function () {
    return {
      commsLogId: "comms-log-table" + uuid(),
      isModalOpen: false,
      commsDTHeaders: [
        "Date",
        "Type",
        "To",
        "CC",
        "From",
        "Subject/Desc",
        "Text",
        "Document",
        "Created",
      ],
      commsDtOptions: {
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        responsive: false,
        deferRender: true,
        autowidth: true,
        scrollX: true,
        order: [[8, "desc"]], // order the non-formatted date as a hidden column
        processing: true,
        // dom:
        //   "<'row'<'col-sm-4'l><'col-sm-8'f>>" +
        //   "<'row'<'col-sm-12'tr>>" +
        //   "<'row'<'col-sm-5'i><'col-sm-7'p>>",
        ajax: {
          url: this.url,
          dataSrc: "",
        },
        columns: [
          {
            title: "Date",
            data: "created",
            render: function (date) {
              return moment(date).format("DD/MM/YYYY HH:mm:ss");
            },
          },
          {
            title: "Type",
            data: "type",
          },
          {
            title: "To",
            data: "to",
          },
          {
            title: "CC",
            data: "cc",
          },
          {
            title: "From",
            data: "fromm",
            render: this.commaToNewline,
          },
          {
            title: "Subject/Desc.",
            data: "subject",
          },
          {
            title: "Text",
            data: "text",
          },
          {
            title: "Documents",
            data: "documents",
            render(values) {
              let result = "";
              (values || []).forEach((val) => {
                let docName = "";
                let url = "";
                if (Array.isArray(val) && val.length > 1) {
                  docName = String(val[0]);
                  url = String(val[1]);
                } else if (typeof val === "string") {
                  url = val;
                  const parts = val.split("/");
                  docName = parts[parts.length - 1];
                  docName = helpers.truncate(docName, {
                    length: 18,
                    omission: "...",
                    separator: " ",
                  });
                }
                if (url) {
                  result += `<a href="${helpers.escapeAttr(url)}" target="_blank"><p>${helpers.escapeAttr(docName)}</p></a><br>`;
                }
              });
              return result;
            },
          },
          {
            title: "Created",
            data: "created",
            visible: false,
          },
        ],
      },
      commsTable: null,
    };
  },
  methods: {
    close: function () {
      this.isModalOpen = false;
    },
    reload: function () {
      // Reload datatable ajax data if possible
      try {
        const dtComp = this.$refs.datatable;
        if (dtComp && dtComp.vmDataTable) {
          const table = dtComp.vmDataTable;
          if (table.ajax && typeof table.ajax.reload === "function") {
            table.ajax.reload();
          } else if (typeof table.draw === "function") {
            table.draw(false);
          }
        }
      } catch (e) {
        console.error("Error reloading comms datatable", e);
      }
    },
  },
};
</script>

<style lang="css">
.btn-file {
  position: relative;
  overflow: hidden;
}
.btn-file input[type="file"] {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 100%;
  min-height: 100%;
  font-size: 100px;
  text-align: right;
  filter: alpha(opacity=0);
  opacity: 0;
  outline: none;
  background: white;
  cursor: inherit;
  display: block;
}
.top-buffer {
  margin-top: 5px;
}
.top-buffer-2x {
  margin-top: 10px;
}
</style>
