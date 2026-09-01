<template id="proposal_dashboard">
  <div class="row">
    <div class="col-sm-12">
      <div class="row">
        <div class="col-md-3">
          <div class="mb-3">
            <label for="">Application Type</label>
            <select class="form-select" v-model="filterProposalActivity">
              <option value="All">All</option>
              <option v-for="a in proposalActivityTypes" :value="a" :key="a">
                {{ a }}
              </option>
            </select>
          </div>
        </div>
        <div class="col-md-3">
          <div class="mb-3">
            <label for="">Status</label>
            <select class="form-select" v-model="filterProposalStatus">
              <option value="All">All</option>
              <option
                v-for="s in proposal_status"
                :value="s.value"
                :key="s.value"
              >
                {{ s.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="col-md-3">
          <label for="">Lodged From</label>
          <input
            id="proposal-lodged-from"
            type="date"
            class="form-control"
            v-model="proposal_lodged_from"
            placeholder="DD/MM/YYYY"
            :max="proposal_lodged_to"
          />
        </div>
        <div class="col-md-3">
          <label for="">Lodged To</label>
          <input
            id="proposal-lodged-to"
            type="date"
            class="form-control"
            v-model="proposal_lodged_to"
            placeholder="DD/MM/YYYY"
            :min="proposal_lodged_from"
          />
        </div>
      </div>
      <div class="row">
        <div v-if="is_external" class="col-md-12">
          <router-link
            style="margin-bottom: 15px; margin-top: 15px"
            class="btn btn-primary float-end"
            :to="{ name: 'apply_proposal' }"
            >{{ newProposalText }}</router-link
          >
        </div>
      </div>
      <div class="row">
        <div class="col-lg-12">
          <div v-if="datatableReady">
            <datatable
              ref="proposal_datatable"
              :id="datatable_id"
              :dtOptions="dt_options"
              :dtHeaders="dt_headers"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import { v4 as uuid } from "uuid";
import datatable from "@/utils/vue/datatable.vue";
import { api_endpoints, constants } from "@/utils/hooks";
import $ from "jquery";
export default {
  name: "ProposalTableDash",
  props: {
    level: {
      type: String,
      required: true,
      validator: function (val) {
        let options = ["internal", "referral", "external"];
        return options.indexOf(val) != -1 ? true : false;
      },
    },
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      assigned_officer_column_name:
        "assigned_officer__first_name, assigned_officer__last_name, assigned_officer__email",
      submitter_column_name:
        "submitter__email, submitter__first_name, submitter__last_name",
      proponent_applicant_column_name:
        "applicant__organisation__name, proxy_applicant__first_name, proxy_applicant__last_name, proxy_applicant__email",
      pBody: "pBody" + uuid(),
      uuid: 0,
      datatable_id: "proposal-datatable-" + uuid(),
      //Profile to check if user has access to process Proposal
      profile: {},
      is_apiary_admin: false,
      // Filters for Proposals
      filterProposalRegion: [],
      filterProposalActivity: "All",
      filterProposalApplicationType: "All",
      filterProposalStatus: "All",
      proposal_lodged_from: "",
      proposal_lodged_to: "",
      filterProposalSubmitter: "All",
      dashboardTitle: "",
      dashboardDescription: "",
      newProposalText: "",
      dateFormat: "DD/MM/YYYY",
      datepickerOptions: {
        format: "DD/MM/YYYY",
        showClear: true,
        useCurrent: false,
        keepInvalid: true,
        allowInputToggle: true,
      },
      external_status: [
        { value: "draft", name: "Draft" },
        { value: "with_assessor", name: "Under Review" },
        { value: "approved", name: "Approved" },
        { value: "declined", name: "Declined" },
      ],
      internal_status: [
        { value: "draft", name: "Draft" },
        { value: "with_assessor", name: "With Assessor" },
        { value: "with_referral", name: "With Referral" },
        {
          value: "with_assessor_requirements",
          name: "With Assessor (Requirements)",
        },
        { value: "with_approver", name: "With Approver" },
        { value: "approved", name: "Approved" },
        { value: "declined", name: "Declined" },
        { value: "discarded", name: "Discarded" },
      ],
      proposalActivityTypes: [],
      proposal_status: [],
      select2Applied: false,
      dt_options: {},
      datatableReady: false,
    };
  },
  components: {
    datatable,
  },
  watch: {
    filterProposalRegion: function () {
      this.$refs.proposal_datatable.vmDataTable.draw();
    },
    filterProposalActivity: function () {
      let vm = this;
      if (vm.filterProposalActivity != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column("activity:name")
          .search(vm.filterProposalActivity)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("activity:name")
          .search("")
          .draw();
      }
    },
    filterProposalApplicationType: function () {
      let vm = this;
      if (vm.filterProposalApplicationType != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column("activity:name")
          .search(vm.filterProposalApplicationType)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("activity:name")
          .search("")
          .draw();
      }
    },
    filterProposalSubmitter: function () {
      let vm = this;
      if (vm.filterProposalSubmitter != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column(vm.submitter_column_name + ":name")
          .search(vm.filterProposalSubmitter)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column(vm.submitter_column_name + ":name")
          .search("")
          .draw();
      }
    },
    filterProposalStatus: function () {
      let vm = this;
      if (vm.filterProposalStatus != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column("status:name")
          .search(vm.filterProposalStatus)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("status:name")
          .search("")
          .draw();
      }
    },
    dateRangeIdentifierForReloadProposalTable: function () {
      this.$refs.proposal_datatable.vmDataTable.draw();
    },
  },
  computed: {
    filterProposalLodgedFrom: {
      get() {
        // If our internal date exists, convert it for submission, etc
        if (this.proposal_lodged_from) {
          return moment(this.proposal_lodged_from, "YYYY-MM-DD").format(
            "DD/MM/YYYY",
          );
        }
        return ""; // Otherwise, return an empty string.
      },
    },
    filterProposalLodgedTo: {
      get() {
        // If our internal date exists, convert it for submission, etc
        if (this.proposal_lodged_to) {
          return moment(this.proposal_lodged_to, "YYYY-MM-DD").format(
            "DD/MM/YYYY",
          );
        }
        return ""; // Otherwise, return an empty string.
      },
    },
    dateRangeIdentifierForReloadProposalTable() {
      return `${this.proposal_lodged_from}|${this.proposal_lodged_to}`;
    },
    dt_headers: function () {
      let columnList = [
        "Number",
        "Application Type",
        "Submitter",
        "Applicant",
        "Status",
        "Lodged on",
      ];
      if (!this.is_external) {
        columnList.push("Assigned Officer");
      }
      columnList.push("Invoice");
      columnList.push("Action");
      return columnList;
    },
    tableColumns: function () {
      let vm = this;
      let columnList = [
        {
          // 1. Number
          data: "id",
          render: function (data, type, full) {
            if (full.migrated) {
              return full.lodgement_number + " (M)";
            } else {
              return full.lodgement_number;
            }
          },
          orderable: true,
          searchable: true,
          defaultContent: "",
        },
      ];
      columnList.push({
        // 3. Activity/Application Type
        data: "activity",
        searchable: false,
        name: "activity",
        defaultContent: "",
      });
      columnList.push(
        {
          // 4. Submitter
          data: "submitter",
          mRender: function (data) {
            if (data) {
              return `${data.first_name} ${data.last_name}`;
            }
            return "";
          },
          name: "submitter__email, submitter__first_name, submitter__last_name",
          searchable: false,
          orderable: false,
          defaultContent: "",
        },
        {
          // 5. Proponent/Applicant
          data: "relevant_applicant_name",
          name: "applicant__organisation__name, proxy_applicant__first_name, proxy_applicant__last_name, proxy_applicant__email",
          searchable: false,
          orderable: false,
          defaultContent: "",
        },
        {
          // 6. Status
          mRender: function (data, type, full) {
            if (vm.is_external) {
              return full.customer_status;
            }
            return full.processing_status;
          },
          searchable: false,
          orderable: false,
          name: "status",
          defaultContent: "",
        },
        {
          // 7. Lodged on
          data: "lodgement_date",
          mRender: function (data) {
            return data != "" && data != null
              ? moment(data).format(vm.dateFormat)
              : "";
          },
          searchable: true,
          defaultContent: "",
        },
      );
      if (!vm.is_external) {
        columnList.push({
          // 8. Assigned Officer
          data: "assigned_officer",
          name: "assigned_officer__first_name, assigned_officer__last_name, assigned_officer__email",
          searchable: false,
          orderable: false,
          defaultContent: "",
        });
      }
      columnList.push({
        // 9. Invoice
        mRender: function (data, type, full) {
          let links = "";
          if (full.fee_invoice_references) {
            for (let item of full.fee_invoice_references) {
              links += "<div>";
              links += `<a href='/ledger-toolkit-api/invoice-pdf/${item.reference}' target='_blank'><i style='color:red;' class='fa fa-file-pdf-o'></i> #${item.reference}</a>`;
              if (!vm.is_external) {
                links += `&nbsp;&nbsp;&nbsp;<a href='${item.ledger_link}' target='_blank'>View Payment</a><br/>`;
              }
              links += "</div>";
            }
          }
          return links;
        },
        name: "invoice_column",
        orderable: false,
        searchable: false,
        defaultContent: "",
      });
      columnList.push({
        // 10. Action
        mRender: function (data, type, full) {
          let links = "";
          if (!vm.is_external) {
            if (full.assessor_process) {
              links += `<a href='/internal/proposal/${full.id}'>Process</a><br/>`;
            } else {
              links += `<a href='/internal/proposal/${full.id}'>View</a><br/>`;
            }
            if (full.can_user_edit && full.processing_status != "Discarded") {
              links += `<a href='#${full.id}' data-discard-proposal='${full.id}'>Discard</a><br/>`;
            }
          } else {
            if (full.can_user_edit) {
              links += `<a href='/external/proposal/${full.id}'>Continue</a><br/>`;
              links += `<a href='#${full.id}' data-discard-proposal='${full.id}'>Discard</a><br/>`;
            } else if (full.can_user_view) {
              links += `<a href='/external/proposal/${full.id}'>View</a><br/>`;
            }
          }
          return links;
        },
        name: "",
        searchable: false,
        orderable: false,
        className: "noexport",
        defaultContent: "",
      });
      console.log(columnList);
      return columnList;
    },

    is_external: function () {
      return this.level == "external";
    },
    is_referral: function () {
      return this.level == "referral";
    },
  },
  methods: {
    set_dt_options: function () {
      this.datatableReady = false;
      let vm = this;
      this.uuid++;
      this.dt_options = {
        destroy: true,
        autoWidth: false,
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        responsive: true,
        serverSide: true,
        lengthMenu: [
          [10, 25, 50, 100],
          [10, 25, 50, 100],
        ],
        order: [[0, "desc"]],
        ajax: {
          url: vm.url,
          dataSrc: "data",

          // adding extra GET params for Custom filtering
          data: function (d) {
            d.regions = vm.filterProposalRegion.join();
            // d.date_from = vm.filterProposalLodgedFrom != '' && vm.filterProposalLodgedFrom != null ? moment(vm.filterProposalLodgedFrom, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
            // d.date_to = vm.filterProposalLodgedTo != '' && vm.filterProposalLodgedTo != null ? moment(vm.filterProposalLodgedTo, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
            d.date_from =
              vm.proposal_lodged_from != "" && vm.proposal_lodged_from != null
                ? moment(vm.proposal_lodged_from, "YYYY-MM-DD").format(
                    "YYYY-MM-DD",
                  )
                : "";
            d.date_to =
              vm.proposal_lodged_to != "" && vm.proposal_lodged_to != null
                ? moment(vm.proposal_lodged_to, "YYYY-MM-DD").format(
                    "YYYY-MM-DD",
                  )
                : "";
            d.application_type = vm.filterProposalApplicationType;
            d.proposal_activity = vm.filterProposalActivity;
            d.submitter = vm.filterProposalSubmitter;
            d.proposal_status = vm.filterProposalStatus;
          },
        },
        dom:
          "<'d-flex align-items-center'<'me-auto'l>fB>" +
          "<'row'<'col-sm-12'tr>>" +
          "<'d-flex align-items-center'<'me-auto'i>p>",
        columnDefs: [
          { responsivePriority: 1, targets: 0 }, // First visible column has top priority (e.g. proposal_number
          { responsivePriority: 2, targets: -1 }, // If the actions is the last entry in columns then this will make it 2nd top priority soo as long as the screen is a decent size it will always be shown
        ],
        buttons: [
          {
            extend: "excelHtml5",
            className: "btn btn-primary me-2 rounded",
            exportOptions: {
              columns: ":not(.noexport)",
              orthogonal: "export",
            },
          },
          {
            extend: "csvHtml5",
            className: "btn btn-primary me-2 rounded",
            exportOptions: {
              columns: ":not(.noexport)",
              orthogonal: "export",
            },
          },
        ],
        columns: vm.tableColumns,
        processing: true,
        initComplete: function () {
          console.log("in initComplete");
          //vm.showHideColumns()
        },
      };
      //});
      this.datatableReady = true;
      this.$nextTick(() => {
        vm.initialiseSearch();
        vm.addEventListeners();
      });
    },

    setDashboardText: function () {
      this.dashboardTitle = "Applications";
      this.dashboardDescription =
        "View existing applications and lodge new ones";
      this.newProposalText = "New Application";
    },

    fetchFilterLists: function () {
      let vm = this;

      fetch(api_endpoints.filter_list).then(
        async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const filterListsProposal = await response.json();
          vm.proposalActivityTypes = filterListsProposal.activities;
          vm.proposal_status =
            vm.level == "internal" ? vm.internal_status : vm.external_status;
        },
        (error) => {
          console.log(error);
        },
      );
    },

    discardProposal: function (proposal_id) {
      let vm = this;
      swal
        .fire({
          title: "Discard Proposal",
          text: "Are you sure you want to discard this proposal?",
          icon: "warning",
          showCancelButton: true,
          confirmButtonText: "Discard Proposal",
          customClass: {
            confirmButton: "btn btn-primary",
            cancelButton: "btn btn-secondary",
          },
        })
        .then(
          (swalresult) => {
            if (swalresult.isConfirmed) {
              fetch(api_endpoints.discard_proposal(proposal_id), {
                method: "DELETE",
                headers: {
                  "Content-Type": "application/json",
                },
              })
                .then(async (response) => {
                  if (!response.ok) {
                    throw new Error(
                      `Discard Proposal failed: ${response.status}`,
                    );
                  }
                  swal.fire({
                    title: "Discarded",
                    text: "Your proposal has been discarded",
                    icon: "success",
                    customClass: {
                      confirmButton: "btn btn-primary",
                    },
                  });
                  vm.$refs.proposal_datatable.vmDataTable.ajax.reload();
                })
                .catch((error) => {
                  console.log(error);
                });
            }
          },
          (error) => {
            console.log(error);
          },
        );
    },
    addEventListeners: function () {
      let vm = this;
      vm.$refs.proposal_datatable.vmDataTable.on(
        "click",
        "a[data-discard-proposal]",
        function (e) {
          e.preventDefault();
          var id = $(this).attr("data-discard-proposal");
          vm.discardProposal(id);
        },
      );
    },
    applySelect2: function () {
      let vm = this;

      if (!vm.select2Applied) {
        $(vm.$refs.filterRegion)
          .select2({
            theme: "bootstrap-5",
            allowClear: true,
            placeholder: "Select Region",
            multiple: true,
          })
          .on("select2:select", function (e) {
            var selected = $(e.currentTarget);
            vm.filterProposalRegion = selected.val();
          })
          .on("select2:unselect", function (e) {
            var selected = $(e.currentTarget);
            vm.filterProposalRegion = selected.val();
          });
        vm.select2Applied = true;
        console.log("select2Applied");
      }
    },
    initialiseSearch: function () {
      this.regionSearch();
      this.submitterSearch();
      this.dateSearch();
    },
    regionSearch: function () {
      let vm = this;
      vm.$refs.proposal_datatable.table.dataTableExt.afnFiltering.push(
        function (settings, data, dataIndex, original) {
          let found = false;
          let filtered_regions = vm.filterProposalRegion;
          if (filtered_regions.length == 0) {
            return true;
          }

          let regions =
            original.region != "" && original.region != null
              ? original.region.split(",")
              : [];

          $.each(regions, (i, r) => {
            if (filtered_regions.indexOf(r) != -1) {
              found = true;
              return false;
            }
          });
          if (found) {
            return true;
          }

          return false;
        },
      );
    },
    submitterSearch: function () {
      let vm = this;
      vm.$refs.proposal_datatable.table.dataTableExt.afnFiltering.push(
        function (settings, data, dataIndex, original) {
          let filtered_submitter = vm.filterProposalSubmitter;
          if (filtered_submitter == "All") {
            return true;
          }
          return filtered_submitter == original.submitter.email;
        },
      );
    },
    dateSearch: function () {
      let vm = this;
      vm.$refs.proposal_datatable.table.dataTableExt.afnFiltering.push(
        function (settings, data, dataIndex, original) {
          let from = vm.filterProposalLodgedFrom;
          let to = vm.filterProposalLodgedTo;
          let val = original.lodgement_date;

          if (from == "" && to == "") {
            return true;
          } else if (from != "" && to != "") {
            return val != null && val != ""
              ? moment()
                  .range(moment(from, vm.dateFormat), moment(to, vm.dateFormat))
                  .contains(moment(val))
              : false;
          } else if (from == "" && to != "") {
            if (val != null && val != "") {
              return moment(to, vm.dateFormat).diff(moment(val)) >= 0
                ? true
                : false;
            } else {
              return false;
            }
          } else if (to == "" && from != "") {
            if (val != null && val != "") {
              return moment(val).diff(moment(from, vm.dateFormat)) >= 0
                ? true
                : false;
            } else {
              return false;
            }
          } else {
            return false;
          }
        },
      );
    },

    fetchProfile: function () {
      let vm = this;
      fetch(api_endpoints.profile)
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          vm.profile = await response.json();
        })
        .catch((error) => {
          console.log(error);
        });
    },

    check_assessor: function (proposal) {
      let vm = this;
      if (proposal.assigned_officer) {
        {
          if (proposal.assigned_officer == vm.profile.full_name) return true;
          else return false;
        }
      } else {
        var assessor = proposal.allowed_assessors.filter(function (elem) {
          return (elem.id = vm.profile.id);
        });

        if (assessor.length > 0) return true;
        else return false;
      }
    },
  },

  mounted: function () {
    console.log("in mounted");
    this.fetchFilterLists();
    this.fetchProfile();
    $('a[data-bs-toggle="collapse"]').on("click", function () {
      var chev = $(this).children()[0];
      window.setTimeout(function () {
        $(chev).toggleClass("fa-chevron-down fa-chevron-up");
      }, 100);
    });

    this.$nextTick(() => {
      //vm.initialiseSearch();
      //vm.addEventListeners();
    });
  },
  created: function () {
    this.set_dt_options();
    this.setDashboardText();
  },
};
</script>
<style scoped>
.dt-buttons {
  float: right;
}
</style>
