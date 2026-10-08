<template lang="html">
  <div class="container">
    <div class="row">
      <div class="col-sm-12">
        <form class="form-horizontal" name="personal_form" method="post">
          <div class="card mb-3">
            <div class="card-header">
              <h5 class="mb-0">
                Apply on behalf of
                <a
                  :href="'#' + pBody"
                  data-bs-toggle="collapse"
                  :aria-controls="pBody"
                >
                  <i class="fa fa-chevron-up float-end"></i>
                </a>
              </h5>
            </div>
            <div class="card-body collapse show" :id="pBody">
              <div class="col-sm-12">
                <div class="mb-3" v-if="!isLoading">
                  <div v-if="!profile.disturbance_organisations.length">
                    <div class="radio">
                      <label :title="individualHasNoLicenceTitle()">
                        <input
                          :disabled="individualDisableApplyRadioButton()"
                          type="radio"
                          name="behalf_of_individual"
                          v-model="behalf_of"
                          value="individual"
                        />
                        On behalf of yourself
                        <span v-html="individualExistingRecordText"></span>
                      </label>
                    </div>
                  </div>
                  <div v-else-if="profile.disturbance_organisations.length > 0">
                    <div
                      v-for="org in profile.disturbance_organisations"
                      class="radio"
                      :key="org.id"
                    >
                      <label :title="orgHasNoLicenceTitle(org)">
                        <input
                          :disabled="orgDisableApplyRadioButton(org)"
                          type="radio"
                          name="behalf_of_org"
                          v-model="behalf_of"
                          :value="org.id"
                        />
                        On behalf of {{ org.name }}
                        <span
                          v-html="org.existing_record_text.notification"
                        ></span>
                      </label>
                    </div>
                  </div>
                  <div v-else-if="behalf_of !== 'individual'">
                    <p style="color: red">
                      You cannot add a New Disturbance because you do not have
                      an associated Organisation. First add an Organisation.
                    </p>
                  </div>
                  <div v-if="profile.is_internal">
                    <input
                          type="radio"
                          name="behalf_of_external"
                          v-model="behalf_of"
                          value="external"
                        />
                        <label>&nbsp;On behalf of an external user or organisation</label>
                  </div>
                </div>
                <div v-show="behalf_of == 'external'">
                  <select 
                    id="person_lookup"  
                    name="person_lookup"  
                    ref="person_lookup" 
                    class="form-control" 
                  ></select>
                </div>
              </div>
            </div>
          </div>

          <div v-if="behalf_of != ''" class="card mb-3">
            <div class="card-header">
              <h5 class="mb-0">
                Apply for
                <a
                  :href="'#' + pBody2"
                  data-bs-toggle="collapse"
                  :aria-controls="pBody2"
                >
                  <i class="fa fa-chevron-up float-end"></i>
                </a>
              </h5>
            </div>
            <div class="card-body collapse show" :id="pBody2">
              <div>
                <label for="" class="form-label">{{ objectTypeLabel }}</label>
                <div class="col-sm-12">
                  <div class="mb-3">
                    <select
                      class="form-select"
                      style="width: 40%"
                      v-model="selected_application_id"
                      @change="chainedSelectAppType(selected_application_id)"
                    >
                      <option value="" selected disabled>
                        {{ objectTypeListLabel }}
                      </option>
                      <option
                        v-for="application_type in applicationTypesList"
                        :value="application_type.value"
                        :key="application_type.value"
                      >
                        {{ application_type.display_text }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div v-if="display_region_selectbox">
                <label for="" class="form-label"
                  >Region *
                  <a :href="region_help_url" target="_blank"
                    ><i class="fa fa-question-circle" style="color: blue"
                      >&nbsp;</i
                    ></a
                  >
                </label>
                <div class="col-sm-12">
                  <div class="mb-3">
                    <select
                      v-model="selected_region"
                      class="form-select"
                      style="width: 40%"
                      @change="chainedSelectDistricts(selected_region)"
                    >
                      <option value="" selected disabled>Select region</option>
                      <option
                        v-for="region in regions"
                        :value="region.value"
                        :key="region.value"
                      >
                        {{ region.text }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div v-if="display_region_selectbox && selected_region">
                <label for="" class="form-label" style="font-weight: normal"
                  >District
                  <a :href="district_help_url" target="_blank"
                    ><i class="fa fa-question-circle" style="color: blue"
                      >&nbsp;</i
                    ></a
                  ></label
                >
                <div class="col-sm-12">
                  <div class="mb-3">
                    <select
                      v-model="selected_district"
                      class="form-select"
                      style="width: 40%"
                    >
                      <option value="" selected disabled>
                        Select district
                      </option>
                      <option
                        v-for="district in districts"
                        :value="district.value"
                        :key="district.value"
                      >
                        {{ district.text }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <div v-if="display_activity_matrix_selectbox">
                <div v-if="activities.length > 0">
                  <label for="" class="form-label"
                    >Activity Type *
                    <a :href="activity_type_help_url" target="_blank"
                      ><i class="fa fa-question-circle" style="color: blue"
                        >&nbsp;</i
                      ></a
                    ></label
                  >
                  <div class="col-sm-12">
                    <div class="mb-3">
                      <select
                        v-model="selected_activity"
                        @change="chainedSelectSubActivities1(selected_activity)"
                        class="form-select"
                        style="width: 40%"
                      >
                        <option value="" selected disabled>
                          Select activity
                        </option>
                        <option
                          v-for="activity in activities"
                          :value="activity.value"
                          :key="activity.value"
                        >
                          {{ activity.text }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>

                <div v-if="sub_activities1.length > 0">
                  <label for="" class="form-label"
                    >Sub Activity 1 *
                    <a :href="sub_activity_1_help_url" target="_blank"
                      ><i class="fa fa-question-circle" style="color: blue"
                        >&nbsp;</i
                      ></a
                    ></label
                  >
                  <div class="col-sm-12">
                    <div class="mb-3">
                      <select
                        v-model="selected_sub_activity1"
                        @change="
                          chainedSelectSubActivities2(selected_sub_activity1)
                        "
                        class="form-select"
                        style="width: 40%"
                      >
                        <option value="" selected disabled>
                          Select sub_activity 1
                        </option>
                        <option
                          v-for="sub_activity1 in sub_activities1"
                          :value="sub_activity1.value"
                          :key="sub_activity1.value"
                        >
                          {{ sub_activity1.text }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>

                <div v-if="sub_activities2.length > 0">
                  <label for="" class="form-label"
                    >Sub Activity 2 *
                    <a :href="sub_activity_2_help_url" target="_blank"
                      ><i class="fa fa-question-circle" style="color: blue"
                        >&nbsp;</i
                      ></a
                    ></label
                  >
                  <div class="col-sm-12">
                    <div class="mb-3">
                      <select
                        v-model="selected_sub_activity2"
                        @change="
                          chainedSelectCategories(selected_sub_activity2)
                        "
                        class="form-select"
                        style="width: 40%"
                      >
                        <option value="" selected disabled>
                          Select sub_activity 2
                        </option>
                        <option
                          v-for="sub_activity2 in sub_activities2"
                          :value="sub_activity2.value"
                          :key="sub_activity2.value"
                        >
                          {{ sub_activity2.text }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>

                <div v-if="categories.length > 0">
                  <label for="" class="form-label"
                    >Category *
                    <a :href="category_help_url" target="_blank"
                      ><i class="fa fa-question-circle" style="color: blue"
                        >&nbsp;</i
                      ></a
                    ></label
                  >
                  <div class="col-sm-12">
                    <div class="mb-3">
                      <select
                        v-model="selected_category"
                        @change="get_approval_level(selected_category)"
                        class="form-select"
                        style="width: 40%"
                      >
                        <option value="" selected disabled>
                          Select category
                        </option>
                        <option
                          v-for="category in categories"
                          :value="category.value"
                          :name="category.approval"
                          :key="category.value"
                        >
                          {{ category.text }}
                        </option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-sm-12">
            <button
              v-if="!creatingProposal"
              :disabled="isDisabled"
              @click.prevent="submit()"
              class="btn btn-primary float-end"
            >
              Continue
            </button>
            <button v-else disabled class="float-end btn btn-primary">
              <i class="fa fa-spin fa-spinner"></i>&nbsp;Creating
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
<script>
import { v4 as uuid } from "uuid";
import { api_endpoints } from "@/utils/hooks";
import utils from "./utils";
import $ from 'jquery'
export default {
  data: function () {
    return {
      proposal: null,
      agent: {},
      behalf_of: "",
      external_applicant: "",
      profile: {
        disturbance_organisations: [],
      },
      loading: [],
      form: null,
      pBody: "pBody" + uuid(),
      pBody2: "pBody2" + uuid(),

      selected_application_id: "",
      selected_application_name: "",
      selected_region: "",
      selected_district: "",
      application_types: [],
      selected_activity: "",
      selected_sub_activity1: "",
      selected_sub_activity2: "",
      selected_category: "",
      regions: [],
      districts: [],
      activity_matrix: [],
      activities: [],
      sub_activities1: [],
      sub_activities2: [],
      categories: [],
      approval_level: "",
      creatingProposal: false,
      display_region_selectbox: false,
      display_activity_matrix_selectbox: false,
      site_url: api_endpoints.site_url.endsWith("/")
        ? api_endpoints.site_url
        : api_endpoints.site_url + "/",
    };
  },
  components: {},
  computed: {
    objectTypeLabel: function () {
      return "Application Type";
    },
    objectTypeListLabel: function () {
      return "Select application type";
    },
    individualExistingRecordText: function () {
      let approvalText = "";
      if (
        this.profile &&
        this.profile.existing_record_text &&
        this.profile.current_apiary_approval === null
      ) {
        approvalText =
          this.profile.existing_record_text.notification +
          " (There is no current Apiary Approval)";
      }
      return approvalText;
    },
    currentApiaryApproval: function () {
      let currentApproval = null;

      if (this.behalf_of === "external" && this.external_applicant !== "") {
        currentApproval = this.external_applicant.current_apiary_approval;
      } else if (
        this.behalf_of === "individual" &&
        this.profile.current_apiary_approval
      ) {
        currentApproval = this.profile.current_apiary_approval;
      } else if (this.behalf_of > 0 && parseInt(this.behalf_of)) {
        for (let organisation of this.profile.disturbance_organisations) {
          if (
            this.behalf_of === organisation.id &&
            organisation.current_apiary_approval
          ) {
            currentApproval = organisation.current_apiary_approval;
          }
        }
      }
      return currentApproval;
    },
    currentApiaryButtonDisabled: function () {
      let currentDisabled = null;
      if (this.behalf_of === "external" && this.external_applicant !== "") {
        this.external_applicant.open_proposal
      } else if (
        this.behalf_of === "individual" &&
        this.profile.existing_record_text.disable_radio_button
      ) {
        currentDisabled =
          this.profile.existing_record_text.disable_radio_button;
      } else if (this.behalf_of > 0 && parseInt(this.behalf_of)) {
        let org = this.profile.disturbance_organisations.find(
          (item) => item.id === this.behalf_of,
        );
        currentDisabled = org.existing_record_text.disable_radio_button;
      }

      return currentDisabled;
    },

    applicationTypesList: function () {
      let returnList = [];
      //TODO update list for external user behalf
      for (let applicationType of this.application_types) {
        if (applicationType.domain_used.toLowerCase() === "apiary") {
          if (
            applicationType.text.toLowerCase() === "apiary" &&
            !this.currentApiaryButtonDisabled
          ) {
            applicationType.display_text = "Apiary Sites";
            returnList.push(applicationType);
          }
          // add Site Transfer if selected applicant has an associated current_apiary_approval
          if (
            applicationType.text.toLowerCase() === "site transfer" &&
            this.currentApiaryApproval &&
            !this.currentApiaryButtonDisabled
          ) {
            applicationType.display_text = "Transfer Apiary Sites";
            returnList.push(applicationType);
          }
          if (
            applicationType.text.toLowerCase() === "temporary use" &&
            this.currentApiaryApproval
          ) {
            // always allow New Temp Use Applications
            applicationType.display_text = "Temporary Use of Apiary Sites";
            returnList.push(applicationType);
          }
        }
      }
      return returnList;
    },
    isLoading: function () {
      return this.loading.length > 0;
    },
    org: function () {
      let vm = this;
      let org_value = "";
      //if (vm.behalf_of != '' || vm.behalf_of != 'other' || vm.behalf_of != 'individual'){
      if (
        vm.behalf_of === "" ||
        vm.behalf_of === "other" ||
        vm.behalf_of === "individual" ||
        vm.behalf_of === "external"
      ) {
        // pass
      } else {
        org_value = vm.profile.disturbance_organisations.find(
          (org) => parseInt(org.id) === parseInt(vm.behalf_of),
        ).name;
      }
      return org_value;
    },
    manyDistricts: function () {
      return this.districts.length > 1;
    },
    isDisabled: function () {
      let vm = this;
      if (
        !["Apiary", "Site Transfer", "Temporary Use"].includes(
          vm.selected_application_name,
        )
      ) {
        if (
          vm.behalf_of == "" || (vm.behalf_of == "external" && vm.external_applicant == "") ||
          vm.selected_application_id == "" ||
          vm.selected_region == "" ||
          vm.approval_level == ""
        ) {
          return true;
        }
      } else {
        if (vm.behalf_of == "" || (vm.behalf_of == "external" && vm.external_applicant == "") || vm.selected_application_id == "") {
          return true;
        }
      }
  
      return false;
    },
  },
  watch: {
    applicationTypesList: function (list) {
      if (list.length === 1) {
        this.selected_application_id = list[0].value;
        this.chainedSelectAppType(list[0].value);
      }
    },
    behalf_of(newVal) {
        if (newVal === 'external') {
            this.$nextTick(() => {
                this.initialisePersonLookup();
            });
        }
    }
  },
  methods: {
    initialisePersonLookup: function(){
      let vm = this;
      const $el = $(vm.$refs.person_lookup);
      if (!$el.hasClass("select2-hidden-accessible")) {
        $el.select2({
            minimumInputLength: 2,
            "theme": "bootstrap-5",
            allowClear: true,
            placeholder:"Select Person or Organisation",
            ajax: {
                url: api_endpoints.person_org_lookup,
                dataType: 'json',
                data: function(params) {
                    var query = {
                        term: params.term,
                        option: "starts_with",
                        type: 'public',
                    }
                    return query;
                },
            },
        }).
        on("select2:select", function (e) {
            vm.external_applicant = Object.assign({}, e.params.data);
            console.log(vm.external_applicant)
        }).
        on("select2:unselect",function () {
            vm.external_applicant = {};
        }).
        on("select2:open",function () {
            const searchField = $('[aria-controls="select2-person_lookup-results"]')
            searchField[0].focus();
        });
      }
    },
    submit: function () {
      let vm = this;
      let text;
      if (
        this.behalf_of === "individual" &&
        this.profile &&
        this.profile.full_name
      ) {
        text =
          "Are you sure you want to create " +
          this.alertText() +
          " proposal on behalf of " +
          this.profile.full_name +
          " ?";
      } else if (this.behalf_of === "external") {
        text =
          "Are you sure you want to create " +
          this.alertText() +
          " proposal on behalf of " +
          this.external_applicant.text +
          " ?";
      } else {
        text =
          "Are you sure you want to create " +
          this.alertText() +
          " proposal on behalf of " +
          vm.org +
          " ?";
      }

      swal
        .fire({
          title: "Create " + vm.selected_application_name,
          text: text,
          icon: "question",
          showCancelButton: true,
          confirmButtonText: "Accept",
          customClass: {
            confirmButton: "btn btn-primary",
            cancelButton: "btn btn-secondary",
          },
        })
        .then((result) => {
          if (result.isConfirmed) {
            vm.createProposal();
          }
        });
    },
    individualDisableApplyRadioButton: function () {
      return (
        this.profile.current_apiary_approval === null &&
        this.profile.existing_record_text.disable_radio_button
      );
    },
    orgDisableApplyRadioButton: function (org) {
      return (
        org.current_apiary_approval === null &&
        org.existing_record_text.disable_radio_button
      );
    },
    individualHasNoLicenceTitle: function () {
      if (this.individualDisableApplyRadioButton()) {
        return this.profile.full_name + " has no current licence";
      }
    },
    orgHasNoLicenceTitle: function (org) {
      if (this.orgDisableApplyRadioButton(org)) {
        return org.name + " has no current licence";
      }
    },

    alertText: function () {
      let vm = this;
      if (vm.selected_application_name == "Apiary") {
        return "an " + vm.selected_application_name.toLowerCase();
      } else {
        return "a " + vm.selected_application_name.toLowerCase();
      }
    },
    createProposal: async function () {
      console.log("createProposal");
      let vm = this;
      vm.creatingProposal = true;

      const payload = {
        behalf_of: vm.behalf_of,
        external_applicant: vm.external_applicant, 
        application: vm.selected_application_id,
        region: vm.selected_region,
        district: vm.selected_district,
        // tenure: vm.selected_tenure,
        activity: vm.selected_activity,
        sub_activity1: vm.selected_sub_activity1,
        sub_activity2: vm.selected_sub_activity2,
        category: vm.selected_category,
        approval_level: vm.approval_level,
        profile: vm.profile.id,
        // Site Transfer
        originating_approval_id: vm.currentApiaryApproval,
        // Temporary Use
        approval_id: vm.currentApiaryApproval,
      };

      try {
        const response = await fetch("/api/proposal.json", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          return response.json().then((err) => {
            throw err;
          });
        }

        const bodyText = await response.text();
        let data;
        try {
          data = JSON.parse(bodyText);
        } catch {
          data = bodyText;
        }

        // Success
        vm.proposal = data;
        vm.$router.push({
          name: "draft_proposal",
          params: { proposal_id: vm.proposal.id },
        });
      } catch (err) {
        console.log(err);
        const bodyText = err.bodyText || err.message || "";

        console.log(bodyText);

        if (
          typeof bodyText === "string" &&
          bodyText.includes("null_applicant_address")
        ) {
          const result = await swal.fire({
            title: "Cannot create application",
            text: "Please add your address",
            icon: "error",
            confirmButtonText: "Ok",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });

          if (result.isConfirmed) {
            vm.$router.push({ name: "account" });
          }
        } else {
          await swal.fire({
            title: "Error",
            text: "Something went wrong creating the proposal.",
            icon: "error",
            confirmButtonText: "Ok",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        }
      } finally {
        vm.creatingProposal = false;
      }
    },
    fetchRegions: function () {
      let vm = this;

      fetch(api_endpoints.regions)
        .then(async (response) => {
          if (!response.ok) {
            return await response.json().then((err) => {
              throw err;
            });
          }
          vm.api_regions = await response.json();
          //console.log('api_regions ' + response.body);

          for (var i = 0; i < vm.api_regions.length; i++) {
            this.regions.push({
              text: vm.api_regions[i].name,
              value: vm.api_regions[i].id,
              districts: vm.api_regions[i].districts,
            });
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },

    searchList: function (id, search_list) {
      /* Searches for dictionary in list */
      for (var i = 0; i < search_list.length; i++) {
        if (search_list[i].value == id) {
          return search_list[i];
        }
      }
      return [];
    },
    chainedSelectDistricts: function (region_id) {
      let vm = this;
      vm.districts = [];

      var api_districts = this.searchList(region_id, vm.regions).districts;
      if (api_districts.length > 0) {
        for (var i = 0; i < api_districts.length; i++) {
          this.districts.push({
            text: api_districts[i].name,
            value: api_districts[i].id,
          });
        }
      }
    },
    fetchApplicationTypes: function () {
      let vm = this;

      fetch("/api/application_types/searchable_application_types")
        .then(async (response) => {
          if (!response.ok) {
            return await response.json().then((err) => {
              throw err;
            });
          }
          vm.api_app_types = await response.json();

          for (var i = 0; i < vm.api_app_types.length; i++) {
            this.application_types.push({
              text: vm.api_app_types[i].name,
              value: vm.api_app_types[i].id,
              domain_used: vm.api_app_types[i].domain_used,
            });
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },
    chainedSelectAppType: function (application_id) {
      /* reset */
      let vm = this;
      vm.selected_region = "";
      vm.selected_district = "";
      vm.selected_activity = "";
      vm.display_region_selectbox = false;
      vm.display_activity_matrix_selectbox = false;

      vm.selected_application_name = this.searchList(
        application_id,
        vm.application_types,
      ).text;
      if (
        ["Apiary", "Site Transfer", "Temporary Use"].includes(
          vm.selected_application_name,
        )
      ) {
        vm.display_region_selectbox = false;
        vm.display_activity_matrix_selectbox = false;
      } else {
        vm.display_region_selectbox = true;
        vm.display_activity_matrix_selectbox = true;
      }
    },

    fetchActivityMatrix: function () {
      let vm = this;
      vm.sub_activities1 = [];
      vm.sub_activities2 = [];
      vm.categories = [];
      vm.approval_level = "";

      fetch(api_endpoints.activity_matrix)
        .then(async (response) => {
          if (!response.ok) {
            return await response.json().then((err) => {
              throw err;
            });
          }
          let matrix_res = await response.json();
          this.activity_matrix = matrix_res.results[0].schema[0];
          this.keys_ordered = matrix_res.results[0].ordered;

          var keys = this.keys_ordered
            ? Object.keys(this.activity_matrix).sort()
            : Object.keys(this.activity_matrix);
          for (var i = 0; i < keys.length; i++) {
            this.activities.push({ text: keys[i], value: keys[i] });
          }
          // vm.fetchRegions();
        })
        .catch((error) => {
          console.log(error);
        });
    },
    chainedSelectSubActivities1: function (activity_name) {
      let vm = this;
      vm.sub_activities1 = [];
      vm.sub_activities2 = [];
      vm.categories = [];
      vm.selected_sub_activity1 = "";
      vm.selected_sub_activity2 = "";
      vm.selected_category = "";
      vm.approval_level = "";

      vm.sub_activities1 = [];
      var [api_activities, res] = this.get_sub_matrix(
        activity_name,
        vm.activity_matrix,
      );
      if (res == "null" || res == null) {
        //for (var i = 0; i < vm.activity_matrix.length; i++) {
        //    if (activity_name == vm.activity_matrix[i]['text']) {
        //        vm.activity_matrix[i]['sub_matrix']
        //    }
        //}
        vm.approval_level = api_activities;
        return;
      } else if (res == "pass") {
        var api_sub_activities = this.get_sub_matrix(
          "pass",
          api_activities[0],
        )[0];
        if ("pass" in api_sub_activities[0]) {
          // go straight to categories widget
          var categories = api_sub_activities[0]["pass"];
          for (var i = 0; i < categories.length; i++) {
            this.categories.push({
              text: categories[i][0],
              value: categories[i][0],
              approval: categories[i][1],
            });
          }
        } else {
          // go to sub_activity2 widget
          for (var j = 0; j < api_sub_activities.length; j++) {
            var key = Object.keys(api_activities[j])[0];
            this.sub_activities1.push({
              text: key,
              value: key,
              sub_matrix: api_activities[j][key],
            });
          }
        }
      } else {
        for (var k = 0; k < api_activities.length; k++) {
          var activityKey = Object.keys(api_activities[k])[0];
          this.sub_activities1.push({
            text: activityKey,
            value: activityKey,
            sub_matrix: api_activities[k][activityKey],
          });
        }
      }
    },

    chainedSelectSubActivities2: function (activity_name) {
      let vm = this;
      vm.sub_activities2 = [];
      vm.categories = [];
      vm.selected_sub_activity2 = "";
      vm.selected_category = "";
      vm.approval_level = "";

      //var api_activities = this.get_sub_matrix(activity_name, vm.sub_activities1[0]['text'])
      var [api_activities, res] = this.get_sub_matrix(
        activity_name,
        vm.sub_activities1,
      );
      if (res == "null" || res == null) {
        vm.approval_level = api_activities;
        return;
      } else if (res == "pass") {
        for (var i = 0; i < api_activities.length; i++) {
          this.categories.push({
            text: api_activities[i][0],
            value: api_activities[i][0],
            approval: api_activities[i][1],
          });
        }
      } else {
        for (var m = 0; m < vm.sub_activities1.length; m++) {
          if (activity_name == vm.sub_activities1[m]["text"]) {
            var api_activities2 = vm.sub_activities1[m]["sub_matrix"];
            for (var j = 0; j < api_activities2.length; j++) {
              var key = Object.keys(api_activities2[j])[0];
              this.sub_activities2.push({
                text: key,
                value: key,
                sub_matrix: api_activities2[j][key],
              });
            }
          }
        }
      }
    },
    chainedSelectCategories: function (activity_name) {
      let vm = this;
      vm.categories = [];
      vm.selected_category = "";
      vm.approval_level = "";

      for (var i = 0; i < vm.sub_activities2.length; i++) {
        if (activity_name == vm.sub_activities2[i]["text"]) {
          var api_categories = vm.sub_activities2[i]["sub_matrix"];
          for (var j = 0; j < api_categories.length; j++) {
            this.categories.push({
              text: api_categories[j][0],
              value: api_categories[j][0],
              approval: api_categories[j][1],
            });
          }
        }
      }
    },

    get_sub_matrix: function (activity_name, sub_activities) {
      // this.sub_activities1[0]['text']
      if (activity_name in sub_activities) {
        if (sub_activities[activity_name].length > 0) {
          if ("pass" in sub_activities[activity_name][0]) {
            return [sub_activities[activity_name], "pass"];
          } else if ("null" in sub_activities[activity_name][0]) {
            var approval_level;
            if (sub_activities[activity_name]["sub_matrix"] == null) {
              approval_level = sub_activities[activity_name][0]["null"][0][0];
            } else {
              approval_level =
                sub_activities[activity_name]["sub_matrix"][0]["null"][0];
            }
            return [approval_level, "null"];
            //return [sub_activities[activity_name], "null"];
          }
        }

        // not a sub_matrix --> this is the main activity_matrix data (as provided by the REST API)
        return [sub_activities[activity_name], true];
      }
      for (var i = 0; i < sub_activities.length; i++) {
        if (activity_name == sub_activities[i]["text"]) {
          var key_sub_matrix = Object.keys(
            sub_activities[i]["sub_matrix"][0],
          )[0];
          if (key_sub_matrix == "null") {
            var sub_approval_level =
              sub_activities[i]["sub_matrix"][0]["null"][0];
            return [sub_approval_level, null];
          } else if (key_sub_matrix == "pass") {
            return [sub_activities[i]["sub_matrix"][0]["pass"], "pass"];
          } else {
            return [sub_activities[i]["sub_matrix"][0], true];
          }
        }
      }
    },
    get_approval_level: function (category_name) {
      let vm = this;
      for (var i = 0; i < vm.categories.length; i++) {
        if (category_name == vm.categories[i]["text"]) {
          vm.approval_level = vm.categories[i]["approval"];
        }
      }
    },
  },
  mounted: function () {
    let vm = this;
    vm.fetchRegions();
    vm.fetchApplicationTypes();
    vm.fetchActivityMatrix();
    vm.initialisePersonLookup();
    vm.form = document.forms.new_proposal;
  },
  beforeRouteEnter: function (to, from, next) {
    let initialisers = [
      utils.fetchProfile(),

      //utils.fetchProposal(to.params.proposal_id)
    ];
    next((vm) => {
      vm.loading.push("fetching profile");
      Promise.all(initialisers).then((data) => {
        vm.profile = data[0];
        //vm.proposal = data[1];
        vm.loading.splice("fetching profile", 1);
      });
    });
  },
};
</script>

<style lang="css" scoped>
input[type="text"],
select {
  width: 40%;
  box-sizing: border-box;

  min-height: 34px;
  /* padding: 0; */
  height: auto;
}

.group-box {
  border-style: solid;
  border-width: thin;
  border-color: #ffffff;
}
.proposalWarning {
  color: red;
}
</style>
