<template lang="html">
  <div class="row col-sm-12" style="margin-bottom: 0.5em">
    <div v-if="is_external">
      <button
        :disabled="!onSiteInformationEnabled"
        class="btn btn-primary float-end"
        @click="openOnSiteInformationModalToAdd"
      >
        Add
      </button>
    </div>
  </div>

  <div class="row col-sm-12">
    <datatable
      ref="on_site_information_table"
      id="on-site-information-table"
      :dtOptions="dtOptions"
      :dtHeaders="dtHeaders"
    />
  </div>

  <div v-if="approval_id">
    <OnSiteInformationModal
      ref="on_site_information_modal"
      :on_site_information="on_site_information_to_edit"
      :approval_id="approval_id"
      :key="modalBindId"
      @on_site_information_added="onSiteInformationAdded"
    />
  </div>
</template>

<script>
import datatable from "@vue-utils/datatable.vue";
import { v4 as uuid } from "uuid";
import { helpers, constants } from "@/utils/hooks";
import OnSiteInformationModal from "./on_site_information_modal.vue";
import $ from "jquery";
import { Popover } from "bootstrap";
export default {
  props: {
    approval_id: {
      type: Number,
      required: true,
      default: 0,
    },
    is_external: {
      type: Boolean,
      default: false,
    },
    is_internal: {
      type: Boolean,
      default: false,
    },
    user_can_interact: {
      type: Boolean,
      default: false,
    },
  },
  data: function () {
    let vm = this;
    return {
      proposal_apiary: null,
      on_site_information_list: [],
      on_site_information_to_edit: {
        id: null,
        apiary_site: null,
        comments: "",
        period_from: null,
        period_to: null,
      },
      modalBindId: null,
      // For Expandable row
      td_expand_class_name: "expand-icon",
      td_collapse_class_name: "collapse-icon",
      expandable_row_class_name: "expandable_row_class_name",
      dtHeaders: [
        "Id",
        "From",
        "To",
        "Site",
        "Comments",
        "The proposed location of the hives",
        "Number of hives proposed to be placed on the site",
        "The names of the people who are expected to be entering the people_names",
        "Flora targeted",
        "Action",
      ],
      dtOptions: {
        serverSide: false,
        searchDelay: 1000,
        autoWidth: false,
        lengthMenu: [
          [10, 25, 50, 100],
          [10, 25, 50, 100],
        ],
        order: [
          [1, "desc"],
          [0, "desc"],
        ],
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        createdCell: helpers.dtPopoverCellFn,
        rowCallback: function () {
          return; // We disable the expander for now
          // console.log('in rowCallback')
          // let row_jq = $(row)
          // row_jq.children().first().addClass(vm.td_expand_class_name)
        },
        responsive: true,
        processing: true,
        columnDefs: [
          { responsivePriority: 1, targets: 0 }, // Id
          { responsivePriority: 2, targets: 9 }, // Action
          { responsivePriority: 3, targets: 1 },
          { responsivePriority: 4, targets: 2 },
          { responsivePriority: 5, targets: 3 },
        ],
        columns: [
          {
            // 0
            mRender: function (data, type, full) {
              if (full.id) {
                return full.id;
              } else {
                return "";
              }
            },
            defaultContent: "",
          },
          {
            // 1
            mRender: function (data, type, full) {
              if (full.period_from) {
                return full.period_from;
              } else {
                return "";
              }
            },
            defaultContent: "",
          },
          {
            // 2
            mRender: function (data, type, full) {
              if (full.period_to) {
                return full.period_to;
              } else {
                return "";
              }
            },
            defaultContent: "",
          },
          {
            // 3
            mRender: function (data, type, full) {
              if (full.apiary_site_id) {
                return full.apiary_site_id;
              } else {
                return "";
              }
            },
            defaultContent: "",
          },
          {
            // 4
            data: "comments",
            mRender: function (data, type) {
              var result = helpers.dtPopover(data);
              return type == "display" ? result : data;
            },
            createdCell: helpers.dtPopoverCellFn,
            defaultContent: "",
          },
          {
            // 5
            data: "hives_loc",
            render: function (data, type) {
              var result = helpers.dtPopover(data);
              return type == "display" ? result : data;
            },
            createdCell: helpers.dtPopoverCellFn,
            defaultContent: "",
          },
          {
            // 6
            mRender: function (data, type, full) {
              if (full.hives_num) {
                return full.hives_num;
              } else {
                return "";
              }
            },
            defaultContent: "",
          },
          {
            // 7
            data: "people_names",
            mRender: function (data, type) {
              var result = helpers.dtPopover(data);
              return type == "display" ? result : data;
            },
            createdCell: helpers.dtPopoverCellFn,
            defaultContent: "",
          },
          {
            // 8
            data: "flora",
            mRender: function (data, type) {
              var result = helpers.dtPopover(data);
              return type == "display" ? result : data;
            },
            createdCell: helpers.dtPopoverCellFn,
            defaultContent: "",
          },
          {
            // 9
            visible: true,
            mRender: function (data, type, full) {
              if (vm.is_external && vm.onSiteInformationEnabled) {
                if (full.action) {
                  return full.action;
                } else {
                  let ret =
                    '<a  class="delete_on_site_information" data-on-site-information-id="' +
                    full.id +
                    '"/>Delete</a>';
                  ret += "<br />";
                  ret +=
                    '<a class="edit_on_site_information" data-on-site-information-id="' +
                    full.id +
                    '"/>Edit<//a>';
                  return ret;
                }
              } else {
                return "";
              }
            },
            defaultContent: "",
          },
        ],
      },
    };
  },
  components: {
    OnSiteInformationModal,
    datatable,
  },
  computed: {
    column_id: () => {},
    column_from: () => {},
    column_to: () => {},
    column_site: () => {},
    column_comments: () => {},
    column_hives_loc: () => {},
    column_hives_num: () => {},
    column_people_names: () => {},
    column_flora: () => {},
    column_action: () => {},
    number_of_columns: function () {
      let num = this.$refs.on_site_information_table.vmDataTable
        .columns(":visible")
        .nodes().length;
      return num;
    },
    onSiteInformationEnabled: function () {
      let enabled = false;
      try {
        if (this.approval_id && this.user_can_interact) {
          enabled = true;
        }
      } catch (err) {
        console.log(err);
      }
      return enabled;
    },
  },
  methods: {
    get_content: function (data) {
      let hives_loc =
        "<tr><td><strong>The proposed location of the hives</strong></td><td>" +
        data.hives_loc +
        "</td></tr>";
      let hives_num =
        "<tr><td><strong>Number of hives proposed to be placed on the site</strong></td><td>" +
        data.hives_num +
        "</td></tr>";
      let people_names =
        "<tr><td><strong>The names of the people who are expected to be entering the site for apiary purposes</strong></td><td>" +
        data.people_names +
        "</td></tr>";
      let flora =
        "<tr><td><strong>Flora targeted</strong></td><td>" +
        data.flora +
        "</td></tr>";

      let contents =
        '<table class="child_table">' +
        hives_loc +
        hives_num +
        people_names +
        flora +
        "</table>";
      return contents;
    },
    onSiteInformationAdded: async function () {
      await this.loadOnSiteInformation(this.approval_id);
      this.constructOnSiteInformationTable();
    },
    openOnSiteInformationModalToAdd: async function () {
      this.openOnSiteInformationModal({
        id: null,
        apiary_site: null,
        comments: "",
        period_from: null,
        period_to: null,
      });
    },
    openOnSiteInformationModal: async function (obj_to_edit) {
      console.log("openOnSiteInformationModal");
      console.log("obj_to_edit: ");
      console.log(obj_to_edit);

      // Refresh the component key
      this.modalBindId = uuid();

      this.on_site_information_to_edit = obj_to_edit;

      try {
        this.$nextTick(() => {
          if (this.$refs.on_site_information_modal) {
            this.$refs.on_site_information_modal.openMe();
          }
        });
      } catch (err) {
        helpers.processError(err);
      }
    },
    constructOnSiteInformationTable: function () {
      // Clear table
      this.$refs.on_site_information_table.vmDataTable.clear().draw();

      // Construct table
      if (this.on_site_information_list.length > 0) {
        for (let i = 0; i < this.on_site_information_list.length; i++) {
          this.addOnSiteInformationToTable(this.on_site_information_list[i]);
        }
      }
    },
    addOnSiteInformationToTable: function (on_site_information) {
      this.$refs.on_site_information_table.vmDataTable.row
        .add(on_site_information)
        .draw();
    },
    addEventListeners: function () {
      let vm = this;
      $("#on-site-information-table").on(
        "click",
        ".delete_on_site_information",
        this.deleteOnSiteInformation,
      );
      $("#on-site-information-table").on(
        "click",
        ".edit_on_site_information",
        this.editOnSiteInformation,
      );
      // this.$refs.on_site_information_table.vmDataTable.on( 'childRow.dt', function () {
      //     console.log('childRow.dt')
      // });

      // $('#example').on('childRow.dt', function(e, show, row) {
      //     console.log((show ? "Showing " : "Hiding ") + "row " + row.index());
      // });

      // Listener for thr row
      //let vm = this
      vm.$refs.on_site_information_table.vmDataTable.on(
        "responsive-display",
        function (e, datatable, row, showHide) {
          if (showHide) {
            // Find the newly rendered child row
            const childRow = $(row.node()).next("tr.child");

            // Initialize popovers inside the child row
            childRow.find('[data-bs-toggle="popover"]').each((_, el) => {
              // Clean up existing instance if any, then create a new one
              const oldInstance = Popover.getInstance(el);
              if (oldInstance) oldInstance.dispose();

              new Popover(el);
            });
          }
        },
      );
      //    let full_data = $row.data()

      //    //------------
      ////    if ($row.child.isShown()){
      ////        $row.child.hide()
      ////    } else {
      ////        $row.child(vm.get_content(full_data)).show()
      ////    }
      //    //------------
      //    let first_td = tr.children().first()
      //    if(first_td.hasClass(vm.td_expand_class_name)){
      //        let $next_elem = tr.next()
      //        if ($next_elem.hasClass('details_row')){
      //            console.log('1')
      //        } else {
      //            console.log('2')
      //            // Expand
      //            let contents = vm.get_content(full_data)

      //            let details_elem = $('<tr class="details_row ' + vm.expandable_row_class_name +'"><td colspan="' + vm.number_of_columns + '">' + contents + '</td></tr>')
      //            details_elem.hide()
      //            details_elem.insertAfter(tr)
      //            details_elem.fadeIn(1000)

      //            // Change icon class name to vm.td_collapse_class_name
      //            first_td.removeClass(vm.td_expand_class_name).addClass(vm.td_collapse_class_name)
      //        }
      //    } else {
      //        let nextElem = tr.next()
      //        // Collapse
      //        if(nextElem.is('tr') & nextElem.hasClass(vm.expandable_row_class_name)){
      //            // Details row is already shown.  Remove it.
      //            nextElem.fadeOut(500, function(){
      //                nextElem.remove()
      //            })
      //        }
      //        // Change icon class name to vm.td_expand_class_name
      //        first_td.removeClass(vm.td_collapse_class_name).addClass(vm.td_expand_class_name)
      //    }
      //})
      //vm.$refs.on_site_information_table.vmDataTable.on('responsive-resize', function(e, datatable, columns) {
      //    // Responsive has changed the visibility of columns in the table in response to a resize or recalculation event.
      //})
      //vm.$refs.on_site_information_table.vmDataTable.on('click', '.more-button', function(e) {
      //    e.preventDefault()
      //    let td_link = $(this)
      //    let tr = td_link.closest('tr')
      //    let $row = vm.$refs.on_site_information_table.vmDataTable.row(tr)
      //    let full_data = $row.data()
      //    //let rowData = tr.data().toArray()[0];
      //    //let fullText = rowData[3];
      //    console.log(full_data)
      //    // showMore: function(node, rowId) {
      //        //let rowData = this.$refs.on_site_information_table.vmDataTable.rows( rowId ).data().toArray()[0];
      //        //let fullText = rowData[3];
      //        //console.log(fullText)
      //        //$( node.parentNode ).text( fullText );
      //    // },
      //})
    },
    editOnSiteInformation: async function (e) {
      console.log("in editOnSiteInformation");

      let on_site_information_id = e.target.getAttribute(
        "data-on-site-information-id",
      );

      console.log("on_site_information_id: " + on_site_information_id);

      let obj_to_edit = {
        id: null,
        apiary_site: null,
        comments: "",
        period_from: null,
        period_to: null,
      };

      for (let i = 0; i < this.on_site_information_list.length; i++) {
        if (this.on_site_information_list[i].id == on_site_information_id) {
          obj_to_edit = this.on_site_information_list[i];
          break;
        }
      }

      this.openOnSiteInformationModal(obj_to_edit);
    },
    deleteOnSiteInformation: async function (e) {
      let vm = this;
      let on_site_information_id = e.target.getAttribute(
        "data-on-site-information-id",
      );

      swal
        .fire({
          title: "Delete on site information",
          text: "Are you sure you want to delete this?",
          icon: "warning",
          showCancelButton: true,
          confirmButtonText: "Yes, delete it",
          customClass: {
            confirmButton: "btn btn-primary",
            cancelButton: "btn btn-secondary",
          },
        })
        .then((result) => {
          if (result.isConfirmed) {
            fetch("/api/on_site_information/" + on_site_information_id + "/", {
              method: "DELETE",
              headers: {
                "Content-Type": "application/json",
              },
            })
              .then(async (response) => {
                if (!response.ok) {
                  throw new Error(
                    `Delete OnSite Information failed: ${response.status}`,
                  );
                }
                await vm.loadOnSiteInformation(this.approval_id);
                vm.constructOnSiteInformationTable();
              })
              .catch((error) => {
                console.log(error);
                swal.fire({
                  title: "Submit Error",
                  text: error,
                  icon: "error",
                  customClass: {
                    confirmButton: "btn btn-primary",
                  },
                });
              });
          }
        });
    },
    loadOnSiteInformation: async function () {
      fetch("/api/approvals/" + this.approval_id + "/on_site_information/")
        .then(async (response) => {
          this.on_site_information_list = await response.json();
          this.constructOnSiteInformationTable();
        })
        .catch((error) => {
          console.log(error);
        });
    },
  },
  created: function () {
    this.loadOnSiteInformation();
  },
  mounted: function () {
    let vm = this;
    this.$nextTick(() => {
      this.constructOnSiteInformationTable();
      vm.addEventListeners();
    });
  },
};
</script>

<style>
.collapse-icon {
  cursor: pointer;
}
.collapse-icon::before {
  top: 5px;
  left: 4px;
  height: 14px;
  width: 14px;
  border-radius: 14px;
  line-height: 14px;
  border: 2px solid white;
  line-height: 14px;
  content: "-";
  color: white;
  background-color: #d33333;
  display: inline-block;
  box-shadow: 0px 0px 3px #444;
  box-sizing: content-box;
  text-align: center;
  text-indent: 0 !important;
  font-family:
    "Courier New",
    Courier monospace;
  margin: 5px;
}
.expand-icon {
  cursor: pointer;
}
.expand-icon::before {
  top: 5px;
  left: 4px;
  height: 14px;
  width: 14px;
  border-radius: 14px;
  line-height: 14px;
  border: 2px solid white;
  line-height: 14px;
  content: "+";
  color: white;
  background-color: #337ab7;
  display: inline-block;
  box-shadow: 0px 0px 3px #444;
  box-sizing: content-box;
  text-align: center;
  text-indent: 0 !important;
  font-family:
    "Courier New",
    Courier monospace;
  margin: 5px;
}
.child_table {
  border-collapse: collapse;
  width: 100%;
}
.child_table tr {
  border-bottom: 1px solid #ccc;
}
.child_table td {
  padding: 0.5em;
}
</style>
