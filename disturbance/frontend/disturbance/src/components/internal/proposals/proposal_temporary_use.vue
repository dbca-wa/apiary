<template lang="html">
  <div v-if="proposal" class="container" id="internalProposal">
    <div class="row">
      <h3 class="mb-3">Application: {{ proposal.lodgement_number }}</h3>
      <h4 class="mb-3">Application Type: {{ proposal.application_type }}</h4>
      <div class="col-md-3">
        <CommsLogs
          :comms_url="comms_url"
          :logs_url="logs_url"
          :comms_add_url="comms_add_url"
          :disable_add_entry="false"
        />
        <div class="mb-3" v-if="canSeeSubmission">
          <div class="card card-default">
            <div class="card-header">Submission</div>
            <div class="card-body py-2">
              <strong>Submitted by</strong><br />
              {{ proposal.submitter }}
            </div>
            <div class="card-body border-top py-2">
              <strong>Lodged on</strong><br />
              {{ formatDate(proposal.lodgement_date) }}
            </div>
          </div>
        </div>

        <div class="card card-default sticky-top">
          <div class="card-header">Workflow</div>
          <div class="card-body py-2">
            <strong>Status</strong><br />
            {{ proposal.processing_status }}
          </div>
          <div v-if="!isFinalised" class="card-body py-2 border-top">
            <div class="row">
              <div class="col-sm-12 top-buffer-s">
                <strong>Currently assigned to</strong>
                <div class="mb-3">
                  <template
                    v-if="proposal.processing_status == 'With Approver'"
                  >
                    <select
                      ref="assigned_officer"
                      :disabled="!canAction"
                      class="form-select"
                      v-model="proposal.assigned_approver"
                    >
                      <option
                        v-for="member in proposal.allowed_assessors"
                        :value="member.id"
                        :key="member.id"
                      >
                        {{ member.first_name }} {{ member.last_name }}
                      </option>
                    </select>
                    <a
                      v-if="
                        canAssess &&
                        proposal.assigned_approver !=
                          proposal.current_assessor.id
                      "
                      @click.prevent="assignRequestUser()"
                      class="actionBtn float-end"
                      >Assign to me</a
                    >
                  </template>
                  <template v-else>
                    <select
                      ref="assigned_officer"
                      :disabled="!canAction"
                      class="form-select"
                      v-model="proposal.assigned_officer"
                    >
                      <option
                        v-for="member in proposal.allowed_assessors"
                        :value="member.id"
                        :key="member.id"
                      >
                        {{ member.first_name }} {{ member.last_name }}
                      </option>
                    </select>
                    <a
                      v-if="
                        canAssess &&
                        proposal.assigned_officer !=
                          proposal.current_assessor.id
                      "
                      @click.prevent="assignRequestUser()"
                      class="actionBtn float-end"
                      >Assign to me</a
                    >
                  </template>
                </div>
              </div>
            </div>
          </div>
          <template
            v-if="
              proposal.processing_status == 'With Assessor (Requirements)' ||
              proposal.processing_status == 'With Approver' ||
              isFinalised
            "
          >
            <div class="card-body py-2 border-top">
              <div class="col-sm-12">
                <strong>Proposal</strong>
                <a
                  class="actionBtn"
                  v-if="!showingProposal"
                  @click.prevent="toggleProposal()"
                  >Show Proposal</a
                >
                <a class="actionBtn" v-else @click.prevent="toggleProposal()"
                  >Hide Proposal</a
                >
              </div>
            </div>
          </template>
          <template
            v-if="proposal.processing_status == 'With Approver' || isFinalised"
          >
            <div class="card-body py-2 border-top">
              <div class="col-sm-12">
                <strong>Requirements</strong>
                <a
                  class="actionBtn"
                  v-if="!showingRequirements"
                  @click.prevent="toggleRequirements()"
                  >Show Requirements</a
                >
                <a
                  class="actionBtn"
                  v-else
                  @click.prevent="toggleRequirements()"
                  >Hide Requirements</a
                >
              </div>
            </div>
          </template>
          <div class="card-body border-top" v-if="!isFinalised && canAction">
            <template v-if="proposal.processing_status == 'With Assessor'">
              <div class="row">
                <div class="col-sm-12">
                  <div class="row mb-2">
                    <strong>Action</strong>
                  </div>
                </div>
              </div>
              <div class="col-sm-12">
                <button
                  style="width: 80%"
                  class="btn btn-primary top-buffer-s"
                  :disabled="proposal.can_user_edit"
                  @click.prevent="amendmentRequest()"
                >
                  Request Amendment
                </button>
              </div>
              <div class="col-sm-12">
                <button
                  style="width: 80%"
                  class="btn btn-primary top-buffer-s"
                  :disabled="proposal.can_user_edit"
                  @click.prevent="issueProposal()"
                >
                  Approve
                </button>
              </div>
              <div class="col-sm-12">
                <button
                  style="width: 80%"
                  class="btn btn-primary top-buffer-s"
                  :disabled="proposal.can_user_edit"
                  @click.prevent="declineProposal()"
                >
                  Decline
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <div class="col-md-9">
        <template
          v-if="proposal.processing_status == 'With Approver' || isFinalised"
        >
          <div v-if="siteTransferTemporaryUse">
            <ApprovalScreenSiteTransferTemporaryUse
              :proposal="proposal"
              @refreshFromResponse="refreshFromResponse"
            />
          </div>
          <div v-else>
            <ApprovalScreen
              :proposal="proposal"
              @refreshFromResponse="refreshFromResponse"
            />
          </div>
        </template>
        <template
          v-if="
            proposal.processing_status == 'With Assessor (Requirements)' ||
            ((proposal.processing_status == 'With Approver' || isFinalised) &&
              showingRequirements)
          "
        >
          <Requirements :proposal="proposal" />
        </template>
        <template
          v-if="canSeeSubmission || (!canSeeSubmission && showingProposal)"
        >
          <FormSection
            :formCollapse="false"
            label="Applicant"
            Index="applicant"
          >
            <template v-if="organisationApplicant">
              <form class="form-horizontal">
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label">Name</label>
                  <div class="col-sm-6">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantName"
                      placeholder=""
                      v-model="proposal.applicant.name"
                    />
                  </div>
                </div>
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label">ABN/ACN</label>
                  <div class="col-sm-6">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantABN"
                      placeholder=""
                      v-model="proposal.applicant.abn"
                    />
                  </div>
                </div>
              </form>
            </template>
            <template v-else>
              <form class="form-horizontal">
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label"
                    >Given Name(s)</label
                  >
                  <div class="col-sm-6">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantFirstName"
                      placeholder=""
                      v-model="proposal.applicant_first_name"
                    />
                  </div>
                </div>
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label"
                    >Last Name</label
                  >
                  <div class="col-sm-6">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantLastName"
                      placeholder=""
                      v-model="proposal.applicant_last_name"
                    />
                  </div>
                </div>
              </form>
            </template>
          </FormSection>

          <FormSection
            :formCollapse="false"
            label="Address Details"
            Index="address_details"
          >
            <form class="form-horizontal">
              <div class="mb-3">
                <label for="" class="col-sm-3 col-form-label">Street</label>
                <div class="col-sm-6">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="street"
                    placeholder=""
                    v-model="applicantAddress.line1"
                  />
                </div>
              </div>
              <div class="mb-3">
                <label for="" class="col-sm-3 col-form-label"
                  >Town/Suburb</label
                >
                <div class="col-sm-6">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="surburb"
                    placeholder=""
                    v-model="applicantAddress.locality"
                  />
                </div>
              </div>
              <div class="mb-3">
                <label for="" class="col-sm-3 col-form-label">State</label>
                <div class="col-sm-2">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="country"
                    placeholder=""
                    v-model="applicantAddress.state"
                  />
                </div>
                <label for="" class="col-sm-2 col-form-label">Postcode</label>
                <div class="col-sm-2">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="postcode"
                    placeholder=""
                    v-model="applicantAddress.postcode"
                  />
                </div>
              </div>
              <div class="mb-3">
                <label for="" class="col-sm-3 col-form-label">Country</label>
                <div class="col-sm-4">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="country"
                    v-model="applicantAddress.country"
                  />
                </div>
              </div>
            </form>
          </FormSection>

          <FormSection
            :formCollapse="false"
            label="Contact Details"
            Index="contact_details"
          >
            <div v-if="organisationApplicant">
              <table
                ref="contacts_datatable"
                :id="contacts_table_id"
                class="mt-2 hover table table-striped table-bordered dt-responsive pt-2"
                cellspacing="0"
                width="100%"
              ></table>
            </div>
            <div v-else>
              <form class="form-horizontal">
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label"
                    >Phone (work)</label
                  >
                  <div class="col-md-8">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantWorkPhone"
                      placeholder=""
                      v-model="proposal.applicant_phone_number"
                    />
                  </div>
                </div>
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label">Mobile</label>
                  <div class="col-md-8">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantMobileNumber"
                      placeholder=""
                      v-model="proposal.applicant_mobile_number"
                    />
                  </div>
                </div>
                <div class="mb-3">
                  <label for="" class="col-sm-3 col-form-label">Email</label>
                  <div class="col-md-8">
                    <input
                      disabled
                      type="text"
                      class="form-control"
                      name="applicantEmail"
                      placeholder=""
                      v-model="proposal.applicant_email"
                    />
                  </div>
                </div>
              </form>
            </div>
          </FormSection>

          <div v-if="proposal">
            <SectionsProposalTemporaryUse
              :proposal="proposal"
              :is_internal="true"
              :is_external="false"
            />
          </div>
        </template>
      </div>
    </div>
    <ProposedDecline
      ref="proposed_decline"
      :processing_status="proposal.processing_status"
      :proposal_id="proposal.id"
      @refreshFromResponse="refreshFromResponse"
    ></ProposedDecline>
    <AmendmentRequest
      ref="amendment_request"
      :proposal_id="proposal.id"
      @refreshFromResponse="refreshFromResponse"
    ></AmendmentRequest>
  </div>
</template>
<script>
import { v4 as uuid } from "uuid";
import ProposedDecline from "./proposal_proposed_decline.vue";
import AmendmentRequest from "./amendment_request.vue";
import Requirements from "./proposal_requirements.vue";
import ApprovalScreen from "./proposal_approval.vue";
import CommsLogs from "@common-utils/comms_logs.vue";
import { api_endpoints, helpers, constants } from "@/utils/hooks";
import SectionsProposalTemporaryUse from "@/components/common/apiary/sections_proposal_temporary_use.vue";
import FormSection from "@/components/forms/section_toggle.vue";
import ApprovalScreenSiteTransferTemporaryUse from "./proposal_approval_site_transfer_temporary_use.vue";
import $ from "jquery";

export default {
  name: "InternalProposalTemporaryUse",
  data: function () {
    let vm = this;
    return {
      detailsBody: "detailsBody" + uuid(),
      addressBody: "addressBody" + uuid(),
      contactsBody: "contactsBody" + uuid(),
      siteLocations: "siteLocations" + uuid(),
      defaultKey: "aho",
      proposal: null,
      original_proposal: null,
      loading: [],
      selected_referral: "",
      referral_text: "",
      approver_comment: "",
      form: null,
      members: [],
      apiaryReferralGroups: [],
      contacts_table_initialised: false,
      initialisedSelects: false,
      showingProposal: false,
      showingRequirements: false,
      hasAmendmentRequest: false,
      state_options: ["requirements", "processing"],
      contacts_table_id: uuid() + "contacts-table",
      contacts_options: {
        language: {
          processing: constants.DATATABLE_PROCESSING_HTML,
        },
        responsive: true,
        ajax: {
          url: vm.contactsURL,
          dataSrc: "",
        },
        columns: [
          {
            data: "id",
            visible: false,
          },
          {
            title: "Name",
            data: "id",
            mRender: function (data, type, full) {
              return full.first_name + " " + full.last_name;
            },
          },
          {
            title: "Phone",
            data: "phone_number",
          },
          {
            title: "Mobile",
            data: "mobile_number",
          },
          {
            title: "Fax",
            data: "fax_number",
          },
          {
            title: "Email",
            data: "email",
          },
        ],
        processing: true,
      },
      contacts_table: null,
      DATE_TIME_FORMAT: "DD/MM/YYYY HH:mm:ss",
      comms_url: helpers.add_endpoint_json(
        api_endpoints.proposals,
        vm.$route.params.proposal_id + "/comms_log",
      ),
      comms_add_url: helpers.add_endpoint_json(
        api_endpoints.proposals,
        vm.$route.params.proposal_id + "/add_comms_log",
      ),
      logs_url: helpers.add_endpoint_json(
        api_endpoints.proposals,
        vm.$route.params.proposal_id + "/action_log",
      ),
      panelClickersInitialised: false,
      sendingReferral: false,
    };
  },
  components: {
    ProposedDecline,
    AmendmentRequest,
    Requirements,
    ApprovalScreen,
    ApprovalScreenSiteTransferTemporaryUse,
    CommsLogs,
    FormSection,
    SectionsProposalTemporaryUse,
  },
  props: {
    proposalId: {
      type: Number,
    },
  },
  computed: {
    contactsURL: function () {
      return this.proposal != null
        ? helpers.add_endpoint_json(
            api_endpoints.organisations,
            this.proposal.applicant.id + "/contacts",
          )
        : "";
    },
    isLoading: function () {
      return this.loading.length > 0;
    },
    csrf_token: function () {
      return helpers.getCookie("csrftoken");
    },
    proposal_form_url: function () {
      if (this.apiaryProposal) {
        return `/api/proposal_apiary/${this.apiaryProposal.id}/assessor_save.json`;
      }
      return "";
    },
    isFinalised: function () {
      return (
        this.proposal.processing_status == "Declined" ||
        this.proposal.processing_status == "Approved"
      );
    },
    canAssess: function () {
      return this.proposal && this.proposal.assessor_mode.assessor_can_assess
        ? true
        : false;
    },
    hasAssessorMode: function () {
      return this.proposal && this.proposal.assessor_mode.has_assessor_mode
        ? true
        : false;
    },
    canAction: function () {
      if (this.proposal.processing_status == "With Approver") {
        return this.proposal &&
          (this.proposal.processing_status == "With Approver" ||
            this.proposal.processing_status == "With Assessor" ||
            this.proposal.processing_status ==
              "With Assessor (Requirements)") &&
          !this.isFinalised &&
          !this.proposal.can_user_edit &&
          (this.proposal.current_assessor.id ==
            this.proposal.assigned_approver ||
            this.proposal.assigned_approver == null) &&
          this.proposal.assessor_mode.assessor_can_assess
          ? true
          : false;
      } else {
        return this.proposal &&
          (this.proposal.processing_status == "With Approver" ||
            this.proposal.processing_status == "With Assessor" ||
            this.proposal.processing_status ==
              "With Assessor (Requirements)") &&
          !this.isFinalised &&
          !this.proposal.can_user_edit &&
          (this.proposal.current_assessor.id ==
            this.proposal.assigned_officer ||
            this.proposal.assigned_officer == null) &&
          this.proposal.assessor_mode.assessor_can_assess
          ? true
          : false;
      }
    },
    canLimitedAction: function () {
      if (this.proposal.processing_status == "With Approver") {
        return this.proposal &&
          (this.proposal.processing_status == "With Assessor" ||
            this.proposal.processing_status == "With Referral" ||
            this.proposal.processing_status ==
              "With Assessor (Requirements)") &&
          !this.isFinalised &&
          !this.proposal.can_user_edit &&
          (this.proposal.current_assessor.id ==
            this.proposal.assigned_approver ||
            this.proposal.assigned_approver == null) &&
          this.proposal.assessor_mode.assessor_can_assess
          ? true
          : false;
      } else {
        return this.proposal &&
          (this.proposal.processing_status == "With Assessor" ||
            this.proposal.processing_status == "With Referral" ||
            this.proposal.processing_status ==
              "With Assessor (Requirements)") &&
          !this.isFinalised &&
          !this.proposal.can_user_edit &&
          (this.proposal.current_assessor.id ==
            this.proposal.assigned_officer ||
            this.proposal.assigned_officer == null) &&
          this.proposal.assessor_mode.assessor_can_assess
          ? true
          : false;
      }
    },
    canSeeSubmission: function () {
      return (
        this.proposal &&
        this.proposal.processing_status != "With Assessor (Requirements)" &&
        this.proposal.processing_status != "With Approver" &&
        !this.isFinalised
      );
    },
    isApprovalLevelDocument: function () {
      return this.proposal &&
        this.proposal.processing_status == "With Approver" &&
        this.proposal.approval_level != null &&
        this.proposal.approval_level_document == null
        ? true
        : false;
    },
    applicant_email: function () {
      return this.proposal &&
        this.proposal.applicant &&
        this.proposal.applicant.email
        ? this.proposal.applicant.email
        : "";
    },
    applicantAddress: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address;
      } else {
        return {};
      }
    },
    organisationApplicant: function () {
      let oApplicant = false;
      if (this.proposal && this.proposal.applicant_type === "organisation") {
        oApplicant = true;
      }
      return oApplicant;
    },
    individualApplicant: function () {
      let iApplicant = false;
      if (this.proposal && this.proposal.applicant_type === "proxy") {
        iApplicant = true;
      }
      return iApplicant;
    },
    apiaryProposal: function () {
      if (this.proposal && this.proposal.proposal_apiary) {
        return this.proposal.proposal_apiary;
      } else {
        return {};
      }
    },
    siteTransferTemporaryUse: function () {
      let returnVal = false;
      if (
        this.proposal &&
        ["Site Transfer", "Temporary Use"].includes(
          this.proposal.application_type,
        )
      ) {
        returnVal = true;
      }
      return returnVal;
    },
  },
  methods: {
    formatDate: function (data) {
      return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
    },
    locationUpdated: function () {
      console.log("in locationUpdated()");
    },
    checkAssessorData: function () {
      //check assessor boxes and clear value of hidden assessor boxes so it won't get printed on approval pdf.

      //select all fields including hidden fields
      //console.log("here");
      var all_fields = $(
        "input[type=text]:required, textarea:required, input[type=checkbox]:required, input[type=radio]:required, input[type=file]:required, select:required",
      );

      all_fields.each(function () {
        var ele = $("[name=" + this.name + "-Assessor]");
        if (ele.length > 0) {
          var visiblity = $("[name=" + this.name + "-Assessor]").is(":visible");
          if (!visiblity) {
            if (ele[0].value != "") {
              //console.log(visiblity, ele[0].name, ele[0].value)
              ele[0].value = "";
            }
          }
        }
      });
    },
    initialiseOrgContactTable: function () {
      console.log("in initialiseOrgContactTable");
      let vm = this;
      if (
        vm.proposal &&
        vm.proposal.applicant &&
        !vm.contacts_table_initialised
      ) {
        vm.contacts_options.ajax.url = helpers.add_endpoint_json(
          api_endpoints.organisations,
          vm.proposal.applicant.id + "/contacts",
        );
        vm.contacts_table = $("#" + vm.contacts_table_id).DataTable(
          vm.contacts_options,
        );
        vm.contacts_table_initialised = true;
      }
    },
    commaToNewline(s) {
      return s.replace(/[,;]/g, "\n");
    },
    issueProposal: function () {
      let vm = this;
      swal
        .fire({
          title: "Approve Proposal",
          text: "Are you sure you want to approve this proposal?",
          icon: "question",
          showCancelButton: true,
          confirmButtonText: "Approve",
          customClass: {
            confirmButton: "btn btn-primary",
            cancelButton: "btn btn-secondary",
          },
        })
        .then(
          (swalresult) => {
            if (swalresult.isConfirmed) {
              let post_url = helpers.add_endpoint_json(
                api_endpoints.proposals,
                vm.proposal.id + "/final_approval_temp_use",
              );
              console.log(post_url);
              fetch(post_url, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
              })
                .then((response) => {
                  if (!response.ok)
                    throw new Error(`HTTP error! Status: ${response.status}`);
                  return response.json();
                })
                .then(() => {
                  vm.$router.push({
                    name: "internal-dashboard",
                  });
                })
                .catch(async (err) => {
                  console.log(err);
                });
            }
          },
          (error) => {
            console.log(error);
          },
        );
    },
    declineProposal: function () {
      let vm = this;
      swal
        .fire({
          title: "Decline Proposal",
          text: "Are you sure you want to decline this proposal?",
          icon: "question",
          showCancelButton: true,
          confirmButtonText: "Decline",
          customClass: {
            confirmButton: "btn btn-primary",
            cancelButton: "btn btn-secondary",
          },
        })
        .then(
          (swalresult) => {
            if (swalresult.isConfirmed) {
              let post_url = helpers.add_endpoint_json(
                api_endpoints.proposals,
                vm.proposal.id + "/final_decline_temp_use",
              );
              console.log(post_url);
              fetch(post_url, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
              })
                .then((response) => {
                  if (!response.ok)
                    throw new Error(`HTTP error! Status: ${response.status}`);
                  return response.json();
                })
                .then(() => {
                  vm.$router.push({
                    name: "internal-dashboard",
                  });
                })
                .catch(async (err) => {
                  console.log(err);
                });
            }
          },
          (err) => {
            console.log(err);
          },
        );
    },
    amendmentRequest: function () {
      let values = "";
      $(".deficiency").each((i, d) => {
        values +=
          $(d).val() != ""
            ? `Question - ${$(d).data("question")}\nDeficiency - ${$(d).val()}\n\n`
            : "";
      });
      this.$refs.amendment_request.amendment.text = values;

      this.$refs.amendment_request.isModalOpen = true;
    },
    highlight_deficient_fields: function (deficient_fields) {
      for (var deficient_field of deficient_fields) {
        $("#" + "id_" + deficient_field).css("color", "red");
      }
    },
    deficientFields() {
      let vm = this;
      let deficient_fields = [];
      $(".deficiency").each((i, d) => {
        if ($(d).val() != "") {
          var name = $(d)[0].name;
          var tmp = name.replace("-comment-field", "");
          deficient_fields.push(tmp);
          //console.log('data', $("#"+"id_" + tmp))
        }
      });
      //console.log('deficient fields', deficient_fields);
      vm.highlight_deficient_fields(deficient_fields);
    },
    save: function () {
      let vm = this;
      vm.checkAssessorData();
      let formData = new FormData(vm.form);
      fetch(vm.proposal_form_url, {
        method: "POST",
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          swal.fire({
            title: "Saved",
            text: "Your proposal has been saved",
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        })
        .catch((err) => {
          console.log(err);
        });
    },

    toggleProposal: function () {
      this.showingProposal = !this.showingProposal;
    },
    toggleRequirements: function () {
      this.showingRequirements = !this.showingRequirements;
    },
    updateAssignedOfficerSelect: function () {
      let vm = this;
      if (vm.proposal.processing_status == "With Approver") {
        $(vm.$refs.assigned_officer).val(vm.proposal.assigned_approver);
        $(vm.$refs.assigned_officer).trigger("change");
      } else {
        $(vm.$refs.assigned_officer).val(vm.proposal.assigned_officer);
        $(vm.$refs.assigned_officer).trigger("change");
      }
    },
    assignRequestUser: function () {
      let vm = this;
      fetch(
        helpers.add_endpoint_json(
          api_endpoints.proposals,
          vm.proposal.id + "/assign_request_user",
        ),
      )
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const data = await response.json();
          vm.proposal = data;
          vm.original_proposal = helpers.copyObject(data);
          vm.proposal.applicant.address =
            vm.proposal.applicant.address != null
              ? vm.proposal.applicant.address
              : {};
          vm.updateAssignedOfficerSelect();
        })
        .catch((error) => {
          vm.proposal = helpers.copyObject(vm.original_proposal);
          vm.proposal.applicant.address =
            vm.proposal.applicant.address != null
              ? vm.proposal.applicant.address
              : {};
          vm.updateAssignedOfficerSelect();
          swal.fire({
            title: "Proposal Error",
            text: error,
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        });
    },
    refreshFromResponse: function (response_data) {
      let vm = this;
      vm.original_proposal = helpers.copyObject(response_data);
      vm.proposal = helpers.copyObject(response_data);
      vm.proposal.applicant.address =
        vm.proposal.applicant.address != null
          ? vm.proposal.applicant.address
          : {};
      vm.$nextTick(() => {
        vm.initialiseAssignedOfficerSelect(true);
        vm.updateAssignedOfficerSelect();
      });
    },
    assignTo: function () {
      let vm = this;
      let unassign;
      let data = {};
      if (vm.proposal.processing_status == "With Approver") {
        unassign = vm.proposal.assigned_approver == null;
        data = { assessor_id: vm.proposal.assigned_approver };
      } else {
        unassign =
          vm.proposal.assigned_officer == null;
        data = { assessor_id: vm.proposal.assigned_officer };
      }
      if (!unassign) {
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposals,
            `${vm.proposal.id}/assign_to`,
          ),
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
          },
        )
          .then(async (response) => {
            if (!response.ok) {
              const errorBody = await response.json();
              throw errorBody;
            }
            const responseBody = await response.json();
            console.log("data", data);
            vm.proposal = responseBody;
            vm.original_proposal = helpers.copyObject(responseBody);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            vm.updateAssignedOfficerSelect();
          })
          .catch((error) => {
            vm.proposal = helpers.copyObject(vm.original_proposal);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            vm.updateAssignedOfficerSelect();
            swal.fire({
              title: "Proposal Error",
              text: error,
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
          });
      } else {
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposals,
            vm.proposal.id + "/unassign",
          ),
        )
          .then(async (response) => {
            if (!response.ok) {
              return response.json().then((err) => {
                throw err;
              });
            }
            const data = await response.json();
            vm.proposal = data;
            vm.original_proposal = helpers.copyObject(data);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            vm.updateAssignedOfficerSelect();
          })
          .catch((error) => {
            vm.proposal = helpers.copyObject(vm.original_proposal);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            vm.updateAssignedOfficerSelect();
            swal.fire({
              title: "Proposal Error",
              text: error,
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
          });
      }
    },
    fetchApiaryReferralGroups: function () {
      this.loading.push("Loading Apiary Referral Groups");
      fetch(api_endpoints.apiary_referral_groups)
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const data = await response.json();
          for (let group of data) {
            this.apiaryReferralGroups.push(group);
          }
          this.loading.splice("Loading Apiary Referral Groups", 1);
        })
        .catch((error) => {
          console.log(error);
          this.loading.splice("Loading Apiary Referral Groups", 1);
        });
    },
    initialiseAssignedOfficerSelect: function (reinit = false) {
      let vm = this;
      if (reinit) {
        $(vm.$refs.assigned_officer).data("select2")
          ? $(vm.$refs.assigned_officer).select2("destroy")
          : "";
      }
      // Assigned officer select
      $(vm.$refs.assigned_officer)
        .select2({
          theme: "bootstrap-5",
          allowClear: true,
          placeholder: "Select Officer",
        })
        .on("select2:select", function (e) {
          var selected = $(e.currentTarget);
          if (vm.proposal.processing_status == "With Approver") {
            vm.proposal.assigned_approver = selected.val();
          } else {
            vm.proposal.assigned_officer = selected.val();
          }
          vm.assignTo();
        })
        .on("select2:unselecting", function () {
          var self = $(this);
          setTimeout(() => {
            self.select2("close");
          }, 0);
        })
        .on("select2:unselect", function () {
          // var selected = $(e.currentTarget);
          if (vm.proposal.processing_status == "With Approver") {
            vm.proposal.assigned_approver = null;
          } else {
            vm.proposal.assigned_officer = null;
          }
          vm.assignTo();
        });
    },
    initialiseSelects: function () {
      let vm = this;
      if (!vm.initialisedSelects) {
        if (vm.$refs.apiary_referral_groups) {
          $(vm.$refs.apiary_referral_groups)
            .select2({
              theme: "bootstrap-5",
              allowClear: true,
              placeholder: "Select Referral",
            })
            .on("select2:select", function (e) {
              var selected = $(e.currentTarget);
              vm.selected_referral = selected.val();
            })
            .on("select2:unselect", function () {
              // var selected = $(e.currentTarget);
              vm.selected_referral = "";
            });
        }
        vm.initialiseAssignedOfficerSelect();
        vm.initialisedSelects = true;
      }
    },
  },
  mounted: function () {
    this.fetchApiaryReferralGroups();
  },
  updated: function () {
    let vm = this;
    if (!vm.panelClickersInitialised) {
      $('.panelClicker[data-bs-toggle="collapse"]').on("click", function () {
        var chev = $(this).children()[0];
        window.setTimeout(function () {
          $(chev).toggleClass("fa-chevron-down fa-chevron-up");
        }, 100);
      });
      vm.panelClickersInitialised = true;
    }
    this.$nextTick(() => {
      vm.initialiseOrgContactTable();
      vm.initialiseSelects();
      vm.form = document.forms.new_proposal;
      if (vm.hasAmendmentRequest) {
        vm.deficientFields();
      }
    });
  },
  created: function () {
    let vm = this;
    fetch(`/api/proposal/${this.proposalId}/internal_proposal.json`)
      .then(async (res) => {
        if (!res.ok) {
          return res.json().then((err) => {
            throw err;
          });
        }
        const data = await res.json();
        this.proposal = data;
        this.original_proposal = helpers.copyObject(data);
        if (this.proposal.applicant) {
          this.proposal.applicant.address =
            this.proposal.applicant.address != null
              ? this.proposal.applicant.address
              : {};
        }

        // Convert from_date and to_date to moment obj
        if (
          vm.proposal.apiary_temporary_use &&
          vm.proposal.apiary_temporary_use.from_date
        ) {
          vm.proposal.apiary_temporary_use.from_date = moment(
            vm.proposal.apiary_temporary_use.from_date,
            "YYYY-MM-DD",
          );
        }
        if (
          vm.proposal.apiary_temporary_use &&
          vm.proposal.apiary_temporary_use.to_date
        ) {
          vm.proposal.apiary_temporary_use.to_date = moment(
            vm.proposal.apiary_temporary_use.to_date,
            "YYYY-MM-DD",
          );
        }

        this.hasAmendmentRequest = this.proposal.hasAmendmentRequest;
      })
      .catch((err) => {
        console.log(err);
        this.loading.splice("Loading Proposal", 1);
      });
  },
  beforeRouteUpdate: function (to, from, next) {
    console.log("beforeRouteUpdate");
    fetch(`/api/proposal/${to.params.proposal_id}.json`)
      .then(async (res) => {
        if (!res.ok) {
          return res.json().then((err) => {
            throw err;
          });
        }
        const data = await res.json();
        next((vm) => {
          vm.proposal = data;
          vm.original_proposal = helpers.copyObject(data);
          if (vm.proposal.applicant) {
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
          }
        });
      })
      .catch((err) => {
        console.log(err);
      });
  },
};
</script>
<style scoped>
.top-buffer-s {
  margin-top: 10px;
}
.actionBtn {
  cursor: pointer;
}
.hidePopover {
  display: none;
}
.separator {
  border: 1px solid;
  margin-top: 15px;
  margin-bottom: 10px;
  width: 100%;
}

.sticky-top {
  top: 1.5em;
}
</style>
