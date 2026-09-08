<template lang="html">
  <div id="proposedIssuanceApproval">
    <modal
      transition="modal fade"
      @ok="ok()"
      @cancel="cancel()"
      :title="title"
      large
    >
      <div class="container-fluid">
        <div class="row">
          <form class="form-horizontal" name="approvalForm">
            <alert v-if="showError" type="danger"
              ><strong>{{ errorString }}</strong></alert
            >
            <div class="col-sm-12">
              <div v-if="!siteTransferApplication">
                <div class="mb-3">
                  <div class="row mb-3">
                    <div class="col-sm-3">
                      <label
                        v-if="processing_status == 'With Approver'"
                        class="form-label float-start"
                        for="Name"
                        >Start Date</label
                      >
                      <label v-else class="form-label float-start" for="Name"
                        >Proposed Start Date</label
                      >
                    </div>
                    <div class="col-sm-9">
                      <template v-if="!startDateCanBeModified">
                        {{ approvalStartDateDisplay }}
                      </template>
                      <template v-else>
                        <div
                          class="input-group date"
                          ref="start_date"
                          style="width: 70%"
                        >
                          <input
                            type="date"
                            class="form-control"
                            name="start_date"
                            placeholder="DD/MM/YYYY"
                            v-model="approval.start_date"
                            :min="today"
                          />
                        </div>
                      </template>
                    </div>
                  </div>
                  <div class="row mb-3" v-show="showstartDateError">
                    <alert class="col-sm-12" type="danger"
                      ><strong>{{ startDateErrorString }}</strong></alert
                    >
                  </div>
                </div>

                <div class="mb-3">
                  <div class="row mb-3">
                    <div class="col-sm-3">
                      <label
                        v-if="processing_status == 'With Approver'"
                        class="form-label float-start"
                        for="Name"
                        >Expiry Date</label
                      >
                      <label v-else class="form-label float-start" for="Name"
                        >Proposed Expiry Date</label
                      >
                    </div>
                    <div class="col-sm-9">
                      <template v-if="!expiryDateCanBeModified">
                        {{ approvalExpiryDateDisplay }}
                      </template>
                      <template v-else>
                        <div
                          class="input-group date"
                          ref="due_date"
                          style="width: 70%"
                        >
                          <input
                            type="date"
                            class="form-control"
                            name="due_date"
                            placeholder="DD/MM/YYYY"
                            v-model="approval.expiry_date"
                            :readonly="is_amendment"
                            :min="approval.start_date"
                          />
                        </div>
                      </template>
                    </div>
                  </div>
                  <div class="row mb-3" v-show="showtoDateError">
                    <alert class="col-sm-12" type="danger"
                      ><strong>{{ toDateErrorString }}</strong></alert
                    >
                  </div>
                </div>
              </div>
              <div v-else>
                <div v-if="creatingSiteTransferTargetApproval" class="mb-3">
                  <div class="row mb-3">
                    <div class="col-sm-3">
                      <label
                        v-if="processing_status == 'With Approver'"
                        class="form-label float-start"
                        for="Name"
                        >Start Date</label
                      >
                      <label v-else class="form-label float-start" for="Name"
                        >Proposed Start Date</label
                      >
                    </div>
                    <div class="col-sm-9">
                      <div
                        class="input-group date"
                        ref="start_date"
                        style="width: 70%"
                      >
                        <input
                          type="date"
                          class="form-control"
                          name="start_date"
                          placeholder="DD/MM/YYYY"
                          v-model="approval.start_date"
                          :min="today"
                        />
                      </div>
                    </div>
                  </div>
                  <div class="row mb-3" v-show="showstartDateError">
                    <alert class="col-sm-12" type="danger"
                      ><strong>{{ startDateErrorString }}</strong></alert
                    >
                  </div>
                </div>

                <div v-if="creatingSiteTransferTargetApproval" class="mb-3">
                  <div class="row mb-3">
                    <div class="col-sm-3">
                      <label
                        v-if="processing_status == 'With Approver'"
                        class="form-label float-start"
                        for="Name"
                        >Expiry Date</label
                      >
                      <label v-else class="form-label float-start" for="Name"
                        >Proposed Expiry Date</label
                      >
                    </div>
                    <div class="col-sm-9">
                      <div
                        class="input-group date"
                        ref="due_date"
                        style="width: 70%"
                      >
                        <input
                          type="date"
                          class="form-control"
                          name="due_date"
                          placeholder="DD/MM/YYYY"
                          v-model="approval.expiry_date"
                          :readonly="is_amendment"
                          :min="approval.start_date"
                        />
                      </div>
                    </div>
                  </div>
                  <div class="row mb-3" v-show="showtoDateError">
                    <alert class="col-sm-12" type="danger"
                      ><strong>{{ toDateErrorString }}</strong></alert
                    >
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <div class="row mb-3">
                  <div class="col-sm-3">
                    <label
                      v-if="processing_status == 'With Approver'"
                      class="form-label float-start"
                      for="Name"
                      >Details</label
                    >
                    <label v-else class="form-label float-start" for="Name"
                      >Proposed Details</label
                    >
                  </div>
                  <div class="col-sm-9">
                    <textarea
                      name="approval_details"
                      class="form-control"
                      v-model="approval.details"
                      rows="10"
                    ></textarea>
                  </div>
                </div>
              </div>
              <div class="mb-3">
                <div class="row mb-3">
                  <div class="col-sm-3">
                    <label
                      v-if="processing_status == 'With Approver'"
                      class="form-label float-start"
                      for="Name"
                      >BCC email</label
                    >
                    <label v-else class="form-label float-start" for="Name"
                      >Proposed BCC email</label
                    >
                  </div>
                  <div class="col-sm-9">
                    <input
                      type="text"
                      class="form-control"
                      name="approval_cc"
                      style="width: 70%"
                      ref="bcc_email"
                      v-model="approval.cc_email"
                    />
                  </div>
                </div>
              </div>

              <div v-for="site in apiary_sites_updated_ordered" :key="site">
                <div v-if="!site.properties.licensed_site">
                  <div class="col-md-12">
                    <div class="row mb-3">
                      <FormSection
                        :formCollapse="true"
                        :label="`Permit details for site ${site.id}`"
                        :Index="`permit_details-` + site.id"
                      >
                        <!-- <div class="row">
                                                    <div class="col-sm-12"> -->
                        <div class="row mb-3">
                          <div class="col-sm-4">
                            <label class="form-label float-start" for="name"
                              >Batch Number</label
                            ><br />
                            <input
                              type="text"
                              class="form-control"
                              name="site_batch_no"
                              style="width: 100%"
                              ref="batch_no"
                              v-model="site.properties.batch_no"
                            />
                          </div>

                          <div class="col-sm-4">
                            <label
                              class="form-label float-start"
                              style="text-align: left"
                              for="name"
                              >Conservation and Parks Commission</label
                            >
                            <input
                              type="date"
                              class="form-control"
                              name="site_cpc_date"
                              placeholder="DD/MM/YYYY"
                              style="width: 100%"
                              ref="cpc_date"
                              v-model="site.properties.approval_cpc_date"
                            />
                          </div>
                          <div class="col-sm-4">
                            <label
                              class="form-label float-start"
                              style="text-align: left"
                              for="name"
                              >Minister for Environment or Delegate</label
                            >
                            <input
                              type="date"
                              class="form-control"
                              name="site_minister_date"
                              placeholder="DD/MM/YYYY"
                              style="width: 100%"
                              ref="minister_date"
                              v-model="site.properties.approval_minister_date"
                            />
                          </div>
                        </div>

                        <div class="row mb-3">
                          <div class="col-sm-4">
                            <label class="form-label float-start" for="name"
                              >Map Reference</label
                            ><br />
                            <input
                              type="text"
                              class="form-control"
                              name="site_map_ref"
                              style="width: 100%"
                              ref="map_ref"
                              v-model="site.properties.map_ref"
                            />
                          </div>
                          <div class="col-sm-4">
                            <label
                              class="form-label float-start"
                              style="text-align: left"
                              for="name"
                              >Forest Block</label
                            >
                            <input
                              type="text"
                              class="form-control"
                              name="site_forest_block"
                              style="width: 100%"
                              ref="forest_block"
                              v-model="site.properties.forest_block"
                            />
                          </div>
                          <div class="col-sm-4">
                            <label
                              class="form-label float-start"
                              style="text-align: left"
                              for="name"
                              >COG</label
                            >
                            <input
                              type="text"
                              class="form-control"
                              name="site_cog"
                              style="width: 100%"
                              ref="cog"
                              v-model="site.properties.cog"
                            />
                          </div>
                        </div>

                        <div class="row mb-3">
                          <div class="col-sm-4">
                            <label class="form-label float-start" for="name"
                              >Apiary Zone</label
                            ><br />
                            <input
                              type="text"
                              class="form-control"
                              name="site_zone"
                              style="width: 100%"
                              ref="zone"
                              v-model="site.properties.zone"
                            />
                          </div>
                          <div class="col-sm-4">
                            <label
                              class="form-label float-start"
                              style="text-align: left"
                              for="name"
                              >Water Catchment Area</label
                            >
                            <input
                              type="text"
                              class="form-control"
                              name="site_catchment"
                              style="width: 100%"
                              ref="catchment"
                              v-model="site.properties.catchment"
                            />
                          </div>
                          <div class="col-sm-4">
                            <label
                              class="form-label float-start"
                              style="text-align: left"
                              for="name"
                              >Nearest Road/Track</label
                            >
                            <input
                              type="text"
                              class="form-control"
                              name="site_roadtrack"
                              style="width: 100%"
                              ref="roadtrack"
                              v-model="site.properties.roadtrack"
                            />
                          </div>
                        </div>

                        <div class="row mb-3">
                          <div class="col-sm-3">
                            <label class="form-label float-start" for="Name"
                              >DRA Permit Required</label
                            >
                          </div>
                          <div class="col-sm-1">
                            <input
                              type="checkbox"
                              class="form-check-input"
                              name="site_dra_permit"
                              ref="dra_permit"
                              v-model="site.properties.dra_permit"
                            />
                          </div>
                        </div>
                      </FormSection>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <div class="row mb-3">
                  <div class="col-sm-12">
                    <div v-if="!siteTransferApplication">
                      <label
                        v-if="submitter_email && applicant_email"
                        class="form-label float-start"
                        for="Name"
                        >After approving this application, the apiary authority
                        will be emailed to
                        {{ proposalNotificationList }}.</label
                      >
                      <label v-else class="form-label float-start" for="Name"
                        >After approving this application, licence will be
                        emailed to {{ submitter_email }}.</label
                      >
                    </div>
                    <div v-else>
                      <label class="form-label float-start"
                        >After approving this application, the originating
                        apiary authority will be emailed to
                        {{ originatingLicenceRecipients }}.</label
                      >
                      <label class="form-label float-start"
                        >After approving this application, the target apiary
                        authority will be emailed to
                        {{ targetLicenceRecipients }}.</label
                      >
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </form>
        </div>

        <template v-if="proposal && !loading_sites">
          <ComponentSiteSelection
            :apiary_sites="apiary_sites_prop"
            :is_internal="true"
            :is_external="false"
            :show_col_site="false"
            :show_col_site_when_submitted="true"
            :show_col_checkbox="true"
            :show_col_status_when_submitted="true"
            :show_col_decision="false"
            :show_col_licensed_site="true"
            :show_col_licensed_site_checkbox="true"
            :key="component_site_selection_key"
            :can_modify="true"
            ref="component_site_selection"
            @apiary_sites_updated="apiarySitesUpdated"
            @featureGeometryUpdated="featureGeometryUpdated"
          />
        </template>
      </div>
      <div v-if="can_preview">
        <div v-if="siteTransferApplication">
          <div>
            Click
            <a href="#" @click.prevent="preview_originating_approval">here</a>
            to preview the originating licence letter.
          </div>
          <div>
            Click
            <a href="#" @click.prevent="preview_target_approval">here</a> to
            preview the target licence letter.
          </div>
        </div>
        <div v-else>
          Click <a href="#" @click.prevent="preview">here</a> to preview the
          licence letter.
        </div>
      </div>

      <template #footer>
        <button
          type="button"
          v-if="issuingApproval"
          disabled
          class="btn btn-primary"
          @click="ok"
        >
          <i class="fa fa-spinner fa-spin"></i> Processing
        </button>
        <span
          v-else-if="ok_button_disabled"
          class="d-inline-block"
          tabindex="0"
          data-bs-toggle="tooltip"
          title="Please select at least one site to issue"
        >
          <button
            type="button"
            style="pointer-events: none"
            class="btn btn-primary"
            @click="ok"
            disabled
          >
            Ok
          </button>
        </span>
        <button v-else type="button" class="btn btn-primary" @click="ok">
          Ok
        </button>
        <button type="button" class="btn btn-secondary" @click="cancel">
          Cancel
        </button>
      </template>
    </modal>
  </div>
</template>

<script>
import { v4 as uuid } from "uuid";
import modal from "@vue-utils/bootstrap-modal.vue";
import alert from "@vue-utils/alert.vue";
import { helpers, api_endpoints } from "@/utils/hooks.js";
import ComponentSiteSelection from "@/components/common/apiary/component_site_selection.vue";
import FormSection from "@/components/forms/section_toggle.vue";
import $ from "jquery";

export default {
  name: "ProposedApiaryIssuance",
  components: {
    modal,
    alert,
    ComponentSiteSelection,
    FormSection,
  },
  props: {
    proposal_apiary_id: {
      type: Number,
      required: true,
    },
    proposal_id: {
      type: Number,
      required: true,
    },
    proposal: {
      type: Object,
      default: null,
    },
    processing_status: {
      type: String,
      required: true,
    },
    proposal_type: {
      type: String,
      required: true,
    },
    isApprovalLevelDocument: {
      type: Boolean,
      required: true,
    },
    submitter_email: {
      type: String,
      required: true,
    },
    applicant_email: {
      type: String,
    },
  },
  data: function () {
    return {
      loading_sites: true,
      isModalOpen: false,
      form: null,
      approval: {},
      state: "proposed_approval",
      issuingApproval: false,
      validation_form: null,
      errors: false,
      toDateError: false,
      startDateError: false,
      errorString: "",
      toDateErrorString: "",
      startDateErrorString: "",
      successString: "",
      success: false,
      apiary_sites_updated: null,
      apiary_licensed_sites_updated: null,
      warningString:
        "Please attach Level of Approval document before issuing Approval",
      component_site_selection_key: "",
      num_of_sites_selected: 0,
      apiary_sites_prop: [],
      issuance_details: [
        {
          batch_no: null,
        },
      ],
    };
  },
  computed: {
    approvalStartDateDisplay: function () {
      let displayDate = null;
      if (
        this.proposal &&
        this.proposal.approval &&
        this.proposal.approval.start_date
      ) {
        displayDate = moment(
          this.proposal.approval.start_date,
          "YYYY-MM-DD",
        ).format("DD/MM/YYYY");
      }
      return displayDate;
    },
    approvalExpiryDateDisplay: function () {
      let displayDate = null;
      if (
        this.proposal &&
        this.proposal.approval &&
        this.proposal.approval.expiry_date
      ) {
        displayDate = moment(
          this.proposal.approval.expiry_date,
          "YYYY-MM-DD",
        ).format("DD/MM/YYYY");
      }
      return displayDate;
    },
    proposalNotificationList: function () {
      let returnVal = `${this.submitter_email} and ${this.applicant_email}.`;
      if (this.submitter_email === this.applicant_email) {
        returnVal = `${this.submitter_email}.`;
      }
      return returnVal;
    },
    ok_button_disabled: function () {
      if (this.num_of_sites_selected > 0) {
        return false;
      }
      return true;
    },
    startDateCanBeModified: function () {
      let returnVal = false;
      if (
        this.proposal &&
        this.proposal.approval &&
        this.proposal.approval.reissued
      ) {
        returnVal = true;
      } else if (this.proposal && !this.proposal.approval) {
        returnVal = true;
      } else if (this.proposal && this.proposal.proposal_type === "Renewal") {
        returnVal = true;
      }
      return returnVal;
    },
    expiryDateCanBeModified: function () {
      let returnVal = false;
      if (
        this.proposal &&
        this.proposal.approval &&
        this.proposal.approval.reissued
      ) {
        returnVal = true;
      } else if (this.proposal && !this.proposal.approval) {
        returnVal = true;
      } else if (this.proposal && this.proposal.proposal_type === "Renewal") {
        returnVal = true;
      }
      return returnVal;
    },
    showError: function () {
      var vm = this;
      return vm.errors;
    },
    showtoDateError: function () {
      var vm = this;
      return vm.toDateError;
    },
    showstartDateError: function () {
      var vm = this;
      return vm.startDateError;
    },
    title: function () {
      return this.processing_status == "With Approver"
        ? "Issue Application"
        : "Propose to Issue";
    },
    is_amendment: function () {
      return this.proposal_type == "Amendment" ? true : false;
    },
    csrf_token: function () {
      return helpers.getCookie("csrftoken");
    },
    can_preview: function () {
      return this.processing_status == "With Approver" ? true : false;
    },
    preview_licence_url: function () {
      return this.proposal_id ? `/preview/licence-pdf/${this.proposal_id}` : "";
    },
    siteTransferApplication: function () {
      let siteTransfer = false;
      if (this.proposal.application_type === "Site Transfer") {
        siteTransfer = true;
      }
      return siteTransfer;
    },
    creatingSiteTransferTargetApproval: function () {
      let creatingApproval = false;
      if (
        !this.siteTransferTargetApprovalExists ||
        (this.proposal.proposal_apiary &&
          this.proposal.proposal_apiary.transferee_id)
      ) {
        creatingApproval = true;
      }
      return creatingApproval;
    },
    siteTransferTargetApprovalExists: function () {
      let targetApprovalExists = false;
      if (
        this.proposal.proposal_apiary &&
        this.proposal.proposal_apiary.target_approval_id
      ) {
        targetApprovalExists = true;
      }
      return targetApprovalExists;
    },
    targetLicenceRecipients: function () {
      if (
        this.proposal.proposal_apiary &&
        this.proposal.proposal_apiary.transferee_email_text
      ) {
        return this.proposal.proposal_apiary.transferee_email_text;
      }
      return "";
    },
    originatingLicenceRecipients: function () {
      if (
        this.proposal.proposal_apiary &&
        this.proposal.proposal_apiary.transferee_email_text &&
        this.proposal.applicant
      ) {
        return this.proposal.applicant.email;
      }
      return "";
    },
    apiary_sites_updated_ordered: function () {
      // adding ordering here on client-side, because iserver-side serializer is ordered for 'apiary_site_id'
      // to allow for PDF ordered output of permits and licences (ApprovalSerializerForLicenceDoc)
      return _.orderBy(this.apiary_sites_updated, "id");
    },
    today() {
      return moment().format("YYYY-MM-DD"); // Format for <input type="date">
    },
  },
  methods: {
    featureGeometryUpdated: function (feature) {
      for (let i = 0; i < this.apiary_sites_updated.length; i++) {
        if (this.apiary_sites_updated[i].id == feature.id) {
          this.apiary_sites_updated[i].coordinates_moved = feature.coordinates;
        }
      }
    },
    apiarySitesUpdated: function (apiary_sites) {
      this.apiary_sites_updated = apiary_sites;

      // Update this.num_of_sites_selected
      let temp = 0;
      for (let i = 0; i < apiary_sites.length; i++) {
        if (apiary_sites[i].checked) {
          temp += 1;
        }
        if (apiary_sites[i].checked) {
          temp += 1;
        }
      }
      this.num_of_sites_selected = temp;
    },
    setApiarySiteCheckedStatuses: function () {
      if (
        this.proposal &&
        this.proposal.proposal_apiary &&
        this.apiary_sites_prop
      ) {
        for (let i = 0; i < this.apiary_sites_prop.length; i++) {
          this.apiary_sites_prop[i].checked =
            this.apiary_sites_prop[i].properties.workflow_selected_status ||
            this.apiary_sites_prop[i].properties.status === "approved";

          if (this.proposal.application_type === "Site Transfer") {
            if (this.is_external) {
              this.apiary_sites_prop[i].checked =
                this.apiary_sites_prop[i].customer_selected;
            } else {
              this.apiary_sites_prop[i].checked =
                this.apiary_sites_prop[i].internal_selected;
            }
          }
        }
      }
    },
    forceToRefreshMap: function () {
      if (this.$refs.component_site_selection) {
        this.$refs.component_site_selection.forceToRefreshMap();
      }
    },
    preview: function () {
      this.previewData();
    },
    preview_originating_approval: function () {
      this.previewData("originating");
    },
    preview_target_approval: function () {
      this.previewData("target");
    },
    post_and_redirect: function (url, postData) {
      /* http.post and ajax do not allow redirect from Django View (post method),
               this function allows redirect by mimicking a form submit.
               usage:  vm.post_and_redirect(vm.application_fee_url, {'csrfmiddlewaretoken' : vm.csrf_token});
            */
      var postFormStr =
        "<form method='POST' target='_blank' name='Preview Licence' action='" +
        url +
        "'>";
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
    ok: function () {
      let vm = this;
      if ($(vm.form).valid()) {
        vm.errors = false;
        vm.sendData();
      } else {
        vm.errorString = "Missing required fields.";
        vm.errors = true;
        this.$nextTick(() => {
          const firstErrorElement = document.querySelector(".error");
          if (firstErrorElement) {
            firstErrorElement.scrollIntoView({
              behavior: "smooth",
              block: "center",
            });

            // Optional: Focus the element for better accessibility
            firstErrorElement.focus?.();
          }
        });
      }
    },
    cancel: function () {
      this.close();
    },
    close: function () {
      this.isModalOpen = false;
      this.approval = {};
      this.errors = false;
      this.toDateError = false;
      this.startDateError = false;
      $(".has-error").removeClass("has-error");
      this.validation_form.resetForm();
    },
    fetchContact: function (id) {
      let vm = this;
      fetch(api_endpoints.contact(id))
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          vm.contact = await response.json();
          vm.isModalOpen = true;
        })
        .catch((error) => {
          console.log(error);
        });
    },
    previewData: function (originating_target = null) {
      let previewWindow = window.open();

      this.approval.preview = true;
      if (originating_target) {
        this.approval.originating_target = originating_target;
      }

      this.approval.apiary_sites = this.apiary_sites_updated;
      if (!this.startDateCanBeModified && !this.siteTransferApplication) {
        // There is an existing licence. Therefore start_date and expiry_date are fixed to that dates
        this.approval.start_date = moment(
          this.proposal.approval.start_date,
          "YYYY-MM-DD",
        ).format("DD/MM/YYYY");
      }
      if (!this.expiryDateCanBeModified && !this.siteTransferApplication) {
        // There is an existing licence. Therefore start_date and expiry_date are fixed to that dates
        this.approval.expiry_date = moment(
          this.proposal.approval.expiry_date,
          "YYYY-MM-DD",
        ).format("DD/MM/YYYY");
      }
      if (
        !this.approval.start_date ||
        this.approval.start_date == "Invalid date"
      ) {
        delete this.approval.start_date;
      }
      if (
        !this.approval.expiry_date ||
        this.approval.expiry_date == "Invalid date"
      ) {
        delete this.approval.expiry_date;
      }
      let approval = JSON.parse(JSON.stringify(this.approval)); // Deep copy

      this.issuingApproval = true;
      if (this.state == "final_approval") {
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposal_apiary,
            this.proposal_apiary_id + "/final_approval",
          ),
          {
            method: "POST",
            body: JSON.stringify(approval),
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": this.csrf_token,
            },
          },
        )
          .then((response) => response.blob())
          .then(function (myBlob) {
            const objectURL = URL.createObjectURL(myBlob);
            previewWindow.location.href = objectURL;
          });
      }
      this.approval.preview = false;
      this.issuingApproval = false;
    },
    sendData: function (preview = false) {
      let vm = this;
      vm.errors = false;
      vm.approval.apiary_sites = vm.apiary_sites_updated;
      if (!this.startDateCanBeModified && !this.siteTransferApplication) {
        // There is an existing licence. Therefore start_date and expiry_date are fixed to that dates
        this.approval.start_date = moment(
          this.proposal.approval.start_date,
          "YYYY-MM-DD",
        ).format("DD/MM/YYYY");
      }
      if (!this.expiryDateCanBeModified && !this.siteTransferApplication) {
        // There is an existing licence. Therefore start_date and expiry_date are fixed to that dates
        this.approval.expiry_date = moment(
          this.proposal.approval.expiry_date,
          "YYYY-MM-DD",
        ).format("DD/MM/YYYY");
      }
      if (
        !this.approval.start_date ||
        this.approval.start_date == "Invalid date"
      ) {
        delete this.approval.start_date;
      }
      if (
        !this.approval.expiry_date ||
        this.approval.expiry_date == "Invalid date"
      ) {
        delete this.approval.expiry_date;
      }

      let approval = JSON.parse(JSON.stringify(vm.approval)); // Deep copy

      vm.issuingApproval = true;
      if (vm.state == "proposed_approval") {
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposals,
            vm.proposal_id + "/proposed_approval",
          ),
          {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded", // emulateJSON
            },
            body: JSON.stringify(approval),
          },
        )
          .then((response) => {
            if (!response.ok) throw response;
            return response.json();
          })
          .then((response) => {
            vm.issuingApproval = false;
            vm.close();
            vm.$emit("refreshFromResponse", response);
            vm.$router.push({ path: "/internal" }); // Navigate to dashboard page after Propose issue.
          })
          .catch(async (error) => {
            vm.errors = true;
            vm.issuingApproval = false;
            try {
              const errData = await error.json();
              vm.errorString = errData;
            } catch {
              vm.errorString = "An unexpected error occurred.";
            }
          });
      } else if (vm.state == "final_approval" && preview) {
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposal_apiary,
            vm.proposal_apiary_id + "/final_approval",
          ),
          {
            method: "POST",
            body: JSON.stringify(approval),
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": vm.csrf_token,
            },
          },
        )
          .then((response) => response.blob())
          .then(function (myBlob) {
            const objectURL = URL.createObjectURL(myBlob);
            let link = document.createElement("a");
            link.href = objectURL;
            link.download = "file.pdf";
            link.click();
            vm.issuingApproval = false;
          });
      } else if (vm.state == "final_approval") {
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposal_apiary,
            vm.proposal_apiary_id + "/final_approval",
          ),
          {
            method: "POST",
            headers: {
              "Content-Type": '"application/json', // emulateJSON
            },
            body: JSON.stringify(approval),
          },
        )
          .then((response) => {
            if (!response.ok) throw response;
            return response.json();
          })
          .then((response) => {
            vm.issuingApproval = false;
            vm.close();
            vm.$emit("refreshFromResponse", response);
          })
          .catch(async (error) => {
            vm.errors = true;
            vm.issuingApproval = false;
            console.log(error);
            try {
              const errData = await error.json();
              vm.errorString = errData;
            } catch {
              vm.errorString = "An unexpected error occurred.";
            }
          });
      }
    },
    addFormValidations: function () {
      let vm = this;
      let rulesVar;
      if (this.siteTransferApplication) {
        rulesVar = {
          approval_details: "required",
        };
      } else {
        rulesVar = {
          start_date: "required",
          due_date: "required",
          approval_details: "required",
        };
      }

      vm.validation_form = $(vm.form).validate({
        rules: rulesVar,
      });
    },
  },
  mounted: function () {
    let vm = this;
    vm.form = document.forms.approvalForm;
    vm.addFormValidations();
    this.component_site_selection_key = uuid();
  },
  created: function () {
    if (this.proposal.application_type === "Site Transfer") {
      console.log("transfer_apiary_sites");
      let url_sites =
        "/api/proposal_apiary/" +
        this.proposal.proposal_apiary.id +
        "/transfer_apiary_sites/";
      fetch(url_sites)
        .then(async (response) => {
          if (response.ok) {
            let transfer_apiary_sites_req = await response.json();
            for (let site of transfer_apiary_sites_req) {
              site.apiary_site.customer_selected = site.customer_selected;
              site.apiary_site.internal_selected = site.internal_selected;
              this.apiary_sites_prop.push(site.apiary_site);
            }
          }
          this.setApiarySiteCheckedStatuses();
          this.loading_sites = false;
        })
        .catch((error) => {
          console.log(error);
          this.loading_sites = false;
        });
    } else {
      //NOTE: this is how we should be loading sites from now on (not bundled with proposal, loaded separetely with a loading_sites boolean)
      let url_sites =
        "/api/proposal_apiary/" +
        this.proposal.proposal_apiary.id +
        "/apiary_sites/";
      console.log("apiary_sites");
      fetch(url_sites)
        .then(async (response) => {
          if (response.ok) {
            let apiary_sites_req = await response.json();
            this.apiary_sites_prop = JSON.parse(
              JSON.stringify(apiary_sites_req),
            ).features;
          }
          this.setApiarySiteCheckedStatuses();
          this.loading_sites = false;
        })
        .catch((error) => {
          console.log(error);
          this.loading_sites = false;
        });
    }
  },
};
</script>

<style lang="css">
.boxed {
  border: 1px solid black;
}
</style>
