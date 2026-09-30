<template id="compliances_dashboard">
  <div class="row">
    <div class="col-sm-12">
      <div class="row">
        <div class="col-md-3">
          <div class="mb-3">
            <label for="">Status</label>
            <select class="form-select" v-model="filterComplianceStatus">
              <option value="All">All</option>
              <option v-for="s in status_values" :value="s" :key="s">
                {{ s }}
              </option>
            </select>
          </div>
        </div>

        <div class="col-md-3">
          <label for="">Due date From</label>
          <input
            id="compliance-due-from"
            type="date"
            class="form-control"
            v-model="compliance_due_from"
            placeholder="DD/MM/YYYY"
          />
        </div>
        <div class="col-md-3">
          <label for="">Due date To</label>
          <input
            id="compliance-due-to"
            type="date"
            class="form-control"
            v-model="compliance_due_to"
            placeholder="DD/MM/YYYY"
            :min="compliance_due_from"
          />
        </div>
      </div>
      <div class="row">
        <div class="col-lg-12" style="margin-top: 25px">
          <div v-if="datatableReady">
            <datatable
              ref="proposal_datatable"
              :id="datatable_id"
              :dtOptions="proposal_options"
              :dtHeaders="proposal_headers"
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
  name: "CompliancesTableDash",
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
    // let vm = this;
    return {
      pBody: "pBody" + uuid(),
      uuid: 0,
      datatable_id: "compliances-datatable-" + uuid(),
      //Profile to check if user has access to process Proposal
      profile: {},
      datatableReady: false,
      // Filters for Proposals
      filterProposalRegion: [],
      filterProposalActivity: "All",
      filterComplianceStatus: "All",
      filterComplianceStartFrom: "",
      filterComplianceStartTo: "",
      compliance_due_from: "",
      compliance_due_to: "",
      filterProposalSubmitter: "All",
      dateFormat: "DD/MM/YYYY",
      datepickerOptions: {
        format: "DD/MM/YYYY",
        showClear: true,
        useCurrent: false,
        keepInvalid: true,
        allowInputToggle: true,
      },
      select2Applied: false,
      proposal_activityTitles: [],
      proposal_regions: [],
      proposal_submitters: [],
      proposal_options: {},
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
          .column("proposal__activity:name")
          .search(vm.filterProposalActivity)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__activity:name")
          .search("")
          .draw();
      }
    },
    filterComplianceStatus: function () {
      this.$refs.proposal_datatable.vmDataTable.draw();
    },
    filterProposalSubmitter: function () {
      this.$refs.proposal_datatable.vmDataTable.draw();
    },
    dateRangeIdentifierForReloadProposalTable: function () {
      this.$refs.proposal_datatable.vmDataTable.draw();
    },
  },
  computed: {
    filterComplianceDueFrom: {
      get() {
        // If our internal date exists, convert it for submission, etc
        if (this.compliance_due_from) {
          return moment(this.compliance_due_from, "YYYY-MM-DD").format(
            "DD/MM/YYYY",
          );
        }
        return ""; // Otherwise, return an empty string.
      },
    },
    filterComplianceDueTo: {
      get() {
        // If our internal date exists, convert it for submission, etc
        if (this.compliance_due_to) {
          return moment(this.compliance_due_to, "YYYY-MM-DD").format(
            "DD/MM/YYYY",
          );
        }
        return ""; // Otherwise, return an empty string.
      },
    },
    dateRangeIdentifierForReloadProposalTable() {
      return `${this.compliance_due_from}|${this.compliance_due_to}`;
    },
    is_external: function () {
      return this.level == "external";
    },
    status_values: function () {
      let under_review_or_with_assessor = "With Assessor";
      if (this.is_external) {
        under_review_or_with_assessor = "Under Review";
      }
      return ["Due", "Future", under_review_or_with_assessor, "Approved"];
    },
    proposal_headers: function () {
      let columnHeaders = [
        "Number",
        "Activity",
        "Due Date",
        "Holder",
        "Licence",
        "Status",
      ];
      if (!this.is_external) {
        columnHeaders.push("Assigned To");
      }
      columnHeaders.push("Action");
      return columnHeaders;
    },
    tableColumns: function () {
      let vm = this;
      let columnList = [
        {
          // 1. Number
          data: "lodgement_number",
          mRender: function (data, type, full) {
            return full.lodgement_number;
          },
          name: "lodgement_number",
          searchable: true,
          defaultContent: "",
        },
      ];
      columnList.push({
        // 3. Activity
        data: "activity",
        name: "proposal__activity",
        defaultContent: "",
      });

      columnList.push(
        {
          // 7. Due Date
          data: "due_date",
          mRender: function (data) {
            return data != "" && data != null
              ? moment(data).format(vm.dateFormat)
              : "";
          },
          defaultContent: "",
          searchable: true,
        },
        {
          // 9. Holder
          data: "holder",
          name: "proposal__applicant__organisation__name",
          defaultContent: "",
          orderable: false,
          searchable: false,
        },
        {
          // 10. Approval/Licence
          data: "approval_lodgement_number",
          mRender: function (data) {
            return `A${data}`;
          },
          name: "approval__lodgement_number",
          defaultContent: "",
        },
        {
          // 11. Status
          data:
            vm.level == "external" ? "customer_status" : "processing_status",
          searchable: false, // There is a filter dropdown for 'Status'
          defaultContent: "",
        },
      );

      if (!vm.is_external) {
        columnList.push({
          // 12. Assigned To
          data: "assigned_to",
          name: "assigned_to__first_name, assigned_to__last_name, assigned_to__email",
          // visible: false
          defaultContent: "",
          orderable: false,
          searchable: false,
        });
      }
      columnList.push({
        // 13. Action
        data: "",
        mRender: function (data, type, full) {
          let links = "";
          if (!vm.is_external) {
            if (
              full.processing_status == "With Assessor" &&
              vm.check_assessor(full)
            ) {
              links += `<a href='/internal/compliance/${full.id}'>Process</a><br/>`;
            } else {
              links += `<a href='/internal/compliance/${full.id}'>View</a><br/>`;
            }
          } else {
            if (full.can_user_view) {
              links += `<a href='/external/compliance/${full.id}'>View</a><br/>`;
            } else {
              links += `<a href='/external/compliance/${full.id}'>Submit</a><br/>`;
            }
          }
          return links;
        },
        name: "",
        className: "noexport",
        defaultContent: "",
      });
      return columnList;
    },
  },
  methods: {
    set_proposal_options: function () {
      this.datatableReady = false;
      let vm = this;
      this.uuid++;
      this.proposal_options = {
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        responsive: true,
        serverSide: true,
        lengthMenu: [
          [10, 25, 50, 100],
          [10, 25, 50, 100],
        ],
        ajax: {
          url: vm.url,
          dataSrc: "data",

          // adding extra GET params for Custom filtering
          data: function (d) {
            d.due_date_from =
              vm.compliance_due_from != "" && vm.compliance_due_from != null
                ? moment(vm.compliance_due_from, "YYYY-MM-DD").format(
                    "YYYY-MM-DD",
                  )
                : "";
            d.due_date_to =
              vm.compliance_due_to != "" && vm.compliance_due_to != null
                ? moment(vm.compliance_due_to, "YYYY-MM-DD").format(
                    "YYYY-MM-DD",
                  )
                : "";
            d.compliance_status = vm.filterComplianceStatus;
            d.region = vm.filterProposalRegion;
            d.proposal_activity = vm.filterProposalActivity;
            d.is_external = vm.is_external;
            d.regions = vm.filterProposalRegion.join();
            //Remove the extra unused parameters from the GET url to reduce the length of the url
            for (var i = 0; i < d.columns.length; i++) {
              delete d.columns[i].search.regex;
            }
          },
        },
        dom:
          "<'d-flex align-items-center'<'me-auto'l>fB>" +
          "<'row'<'col-sm-12'tr>>" +
          "<'d-flex align-items-center'<'me-auto'i>p>",
        /*
                buttons:[
                'excel', 'csv', ],
                */
        columnDefs: [
          { responsivePriority: 1, targets: 0 }, // First visible column has top priority (e.g. proposal_number
          { responsivePriority: 2, targets: -5 }, // If the actions is the last entry in columns then this will make it 2nd top priority soo as long as the screen is a decent size it will always be shown
        ],
        buttons: [
          {
            extend: "excel",
            className: "btn btn-primary me-2 rounded",
            exportOptions: {
              columns: ":not(.noexport)",
              orthogonal: "export",
            },
          },
          {
            extend: "csv",
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
          //vm.showHideColumns()
        },
      };
      this.datatableReady = true;
      this.$nextTick(() => {
        this.initialiseSearch();
      });
    },
    fetchFilterLists: function () {
      let vm = this;

      fetch(api_endpoints.filter_list_compliances).then(
        async (response) => {
          let filter_lists_compliance = await response.json();
          vm.proposal_regions = filter_lists_compliance.regions;
          vm.proposal_activityTitles = filter_lists_compliance.activities;
          vm.status =
            vm.level == "external" ? vm.external_status : vm.internal_status;
        },
        (error) => {
          console.log(error);
        },
      );
      //console.log(vm.regions);
    },
    initialiseSearch: function () {
      this.regionSearch();
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
          let from = vm.filterComplianceDueFrom;
          let to = vm.filterComplianceDueTo;
          let val = original.due_date;

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
      fetch(api_endpoints.profile).then(
        async (response) => {
          vm.profile = await response.json();
        },
        (error) => {
          console.log(error);
        },
      );
    },
    check_assessor: function (compliance) {
      let vm = this;
      if (compliance.allowed_assessors) {
        var assessor = compliance.allowed_assessors.filter(function (elem) {
          return elem.id == vm.profile.id;
        });

        if (assessor.length > 0) {
          //console.log(proposal.id, assessor)
          return true;
        } else return false;
      } else {
        return false;
      }
    },
  },
  created: function () {
    this.set_proposal_options();
  },
  mounted: function () {
    //console.log('in mounted')
    let vm = this;
    vm.fetchFilterLists();
    vm.fetchProfile();
    $('a[data-bs-toggle="collapse"]').on("click", function () {
      var chev = $(this).children()[0];
      window.setTimeout(function () {
        $(chev).toggleClass("fa-chevron-down fa-chevron-up");
      }, 100);
    });
    /*
        if(vm.is_external){
            var column = vm.$refs.proposal_datatable.vmDataTable.columns(8); //Hide 'Assigned To column for external'
            column.visible(false);
        }
        */
    /*
        this.$nextTick(() => {
            this.initialiseSearch();
            this.addEventListeners();
        });
        */
  },
};
</script>
<style></style>
