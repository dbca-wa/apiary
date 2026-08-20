<template id="proposal_dashboard">
  <div class="row">
    <div class="col-sm-12">
      <div class="row">
        <div class="col-md-3">
          <div class="mb-3">
            <label for="">Application Type</label>
            <select class="form-select" v-model="filterProposalActivity">
              <option value="All">All</option>
              <option v-for="a in proposal_activityTitles" :value="a" :key="a">
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
          <div class="input-group date" ref="proposalDateFromPicker">
            <!-- <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterProposalLodgedFrom">
                        <span class="input-group-addon">
                            <span class="fa fa-calendar"></span>
                        </span> -->
            <input
              id="proposal-lodged-from"
              type="date"
              class="form-control"
              v-model="proposal_lodged_from"
              placeholder="DD/MM/YYYY"
              :max="proposal_lodged_to"
            />
          </div>
        </div>
        <div class="col-md-3">
          <label for="">Lodged To</label>
          <div class="input-group date" ref="proposalDateToPicker">
            <!-- <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterProposalLodgedTo">
                        <span class="input-group-addon">
                            <span class="fa fa-calendar"></span>
                        </span> -->
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
      </div>
      <div class="row">
        <div class="col-lg-12">
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
</template>
<script>
import { v4 as uuid } from "uuid";
import datatable from "@/utils/vue/datatable.vue";
import { api_endpoints, constants } from "@/utils/hooks";
import $ from "jquery";

export default {
  name: "RefferralsTableDash",
  props: {
    url: {
      type: String,
      required: true,
    },
  },

  data() {
    let vm = this;
    return {
      pBody: "pBody" + uuid(),
      datatable_id: "proposal-datatable-" + uuid(),
      select2Applied: false,
      // Filters for Proposals
      filterProposalRegion: [],
      filterProposalActivity: "All",
      filterProposalApplicationType: "All",
      filterProposalStatus: "All",
      // filterProposalLodgedFrom: '',
      // filterProposalLodgedTo: '',
      proposal_lodged_from: "",
      proposal_lodged_to: "",
      filterProposalSubmitter: "All",
      dateFormat: "DD/MM/YYYY",
      proposal_status: [],
      proposal_activityTitles: [],
      proposal_applicationTypes: [],
      proposal_regions: [],
      proposal_submitters: [],
      //proposal_headers:["Number","Region","Activity","Title","Submitter","Proponent","Status","Lodged on","Action","Template Group"],
      proposal_options: {
        customProposalSearch: true,
        tableID: "proposal-datatable-" + uuid(),
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        responsive: false, // false as applying scrolX instead to manage responsiveness and column visibility
        scrollX: true,
        fixedColumns: {
          leftColumns: 1,
          end: 1,
        },
        serverSide: true,
        lengthMenu: [
          [10, 25, 50, 100],
          [10, 25, 50, 100],
        ],
        order: [[0, "desc"]],
        dom:
          "<'d-flex align-items-center'<'me-auto'l>fB>" +
          "<'row'<'col-sm-12'tr>>" +
          "<'d-flex align-items-center'<'me-auto'i>p>",
        columnDefs: [
          { responsivePriority: 1, targets: 0 }, // First visible column has top priority (e.g. proposal_number
          { responsivePriority: 2, targets: -5 }, // If the actions is the last entry in columns then this will make it 2nd top priority soo as long as the screen is a decent size it will always be shown
        ],
        buttons: [],
        ajax: {
          url: vm.url,
          dataSrc: "data",

          // adding extra GET params for Custom filtering
          data: function (d) {
            d.regions = vm.filterProposalRegion.join();
            //d.processing_status = vm.filterProposalStatus;
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
        columns: [
          {
            data: "proposal",
            mRender: function (data, type, full) {
              let tick;
              if (full.can_be_processed) {
                tick =
                  "<i class='bi bi-exclamation-circle-fill ms-1' style='color:#FFBF00'></i>";
              } else {
                tick =
                  "<i class='bi bi-check-circle-fill' style='color:green'></i>";
              }
              return full.proposal_lodgement_number + tick;
            },
            name: "proposal__id, proposal__lodgement_number",
            defaultContent: "",
          },
          {
            data: "region",
            searchable: false, // handles by filter_queryset override method - class ProposalFilterBackend
            visible: false,
            defaultContent: "",
          },
          {
            data: "activity",
            name: "proposal__activity",
            //searchable: false, // handles by filter_queryset override method - class ProposalFilterBackend
            defaultContent: "",
          },
          {
            data: "title",
            name: "proposal__title",
            visible: false,
            defaultContent: "",
          },
          {
            data: "submitter",
            mRender: function (data) {
              if (data) {
                return `${data.first_name} ${data.last_name}`;
              }
              return "";
            },
            name: "proposal__submitter__email",
            defaultContent: "",
          },
          /*
                    {
                        data: "applicant",
                        mRender:function (data,type,full) {
                            if (data) {
                                return `${data}`;
                            } else if (full.proposal_proxy_applicant) {
                                return full.proposal_proxy_applicant.name;
                            } else {
                                return '';
                            }
                        },
                        name: "proposal__applicant__organisation__name",
                    },
                    */
          {
            data: "relevant_applicant_name",
            name: "proposal__applicant__organisation__name",
            defaultContent: "",
          },
          {
            data: "processing_status",
            name: "proposal__processing_status",
            defaultContent: "",
          },
          {
            data: "assigned_officer",
            name: "assigned_officer",
            mRender: function (data) {
              if (data) {
                return `${data.first_name} ${data.last_name}`;
              }
              return "";
            },
            visible: false,
            searchable: false,
            defaultContent: "",
          },
          {
            data: "proposal_lodgement_date",
            mRender: function (data) {
              return data != "" && data != null
                ? moment(data).format(vm.dateFormat)
                : "";
            },
            name: "proposal__lodgement_date",
            defaultContent: "",
          },
          {
            data: "",
            mRender: function (data, type, full) {
              let links = "";
              links += full.can_be_processed
                ? `<a href='/internal/proposal/${full.proposal}/referral/${full.id}'>Process</a><br/>`
                : `<a href='/internal/proposal/${full.proposal}/referral/${full.id}'>View</a><br/>`;
              return links;
            },
            searchable: false,
            orderable: false,
            name: "",
            defaultContent: "",
          },
          { data: "can_be_processed", visible: false, defaultContent: "" },
          {
            data: "proposal_lodgement_number",
            visible: false,
            defaultContent: "",
          },
          { data: "id", visible: false, defaultContent: "" },
          {
            data: "template_group",
            searchable: false,
            orderable: false,
            visible: false,
            defaultContent: "",
          },
        ],
        processing: true,
        initComplete: function () {
          // set column visibility and headers according to template group
          let assignedOfficerColumn =
            vm.$refs.proposal_datatable.vmDataTable.column(
              "assigned_officer:name",
            );
          assignedOfficerColumn.visible(true);
        },
      },
    };
  },
  components: {
    datatable,
  },
  watch: {
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
    filterProposalApplicationType: function () {
      let vm = this;
      if (vm.filterProposalApplicationType != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__activity:name")
          .search(vm.filterProposalApplicationType)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__activity:name")
          .search("")
          .draw();
      }
    },
    filterProposalStatus: function () {
      let vm = this;
      if (vm.filterProposalStatus != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__processing_status:name")
          .search(vm.filterProposalStatus)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__processing_status:name")
          .search("")
          .draw();
      }
    },
    filterProposalRegion: function () {
      this.$refs.proposal_datatable.vmDataTable.draw();
    },
    filterProposalSubmitter: function () {
      //this.$refs.proposal_datatable.vmDataTable.draw();
      let vm = this;
      if (vm.filterProposalSubmitter != "All") {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__submitter__email:name")
          .search(vm.filterProposalSubmitter)
          .draw();
      } else {
        vm.$refs.proposal_datatable.vmDataTable
          .column("proposal__submitter__email:name")
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
        if (this.proposal_lodged_from) {
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
    dashboardTitle: function () {
      return "Applications referred to me";
    },
    proposal_headers: function () {
      return [
        "Number",
        "Region",
        "Application Type",
        "Title",
        "Submitter",
        "Applicant",
        "Status",
        "Assigned Officer",
        "Lodged on",
        "Action",
        "Template Group",
      ];
    },
  },
  methods: {
    fetchFilterLists: function () {
      let vm = this;

      fetch(api_endpoints.filter_list_referrals)
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const filter_list_ref = await response.json();
          vm.proposal_regions = filter_list_ref.regions;
          //vm.proposal_districts = response.body.districts;
          vm.proposal_activityTitles = filter_list_ref.application_types;
          vm.proposal_submitters = filter_list_ref.submitters;
          vm.proposal_status = filter_list_ref.processing_status_choices;
        })
        .catch((error) => {
          console.log(error);
        });
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
  },
  mounted: function () {
    let vm = this;
    vm.fetchFilterLists();
    $('a[data-bs-toggle="collapse"]').on("click", function () {
      var chev = $(this).children()[0];
      window.setTimeout(function () {
        $(chev).toggleClass("fa-chevron-down fa-chevron-up");
      }, 100);
    });
    this.$nextTick(() => {
      vm.addEventListeners();
      //vm.initialiseSearch();
    });
  },
  updated: function () {
    this.$nextTick(() => {
      this.initialiseSearch();
      //this.addEventListeners();
    });
  },
};
</script>
<style scoped></style>
