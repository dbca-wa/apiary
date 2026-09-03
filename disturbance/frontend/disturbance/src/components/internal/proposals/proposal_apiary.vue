<template lang="html">
  <div v-if="proposal" class="container" id="internalProposal">
    <div class="row">
      <h3>Application: {{ proposal.lodgement_number }}</h3>
      <h4 class="mb-3">Application Type: {{ proposal.activity }}</h4>
      <div v-if="!proposal.apiary_group_application_type">
        <h4 class="mb-3">Approval Level: {{ proposal.approval_level }}</h4>
      </div>
      <div class="col-md-3">
        <CommsLogs
          :comms_url="comms_url"
          :logs_url="logs_url"
          :comms_add_url="comms_add_url"
          :disable_add_entry="false"
        />

        <div v-if="canSeeSubmission" class="card card-default">
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

        <div class="card card-default sticky-top mt-3">
          <div class="card-header">Workflow</div>
          <div class="card-body py-2">
            <strong>Status</strong><br />
            {{ proposal.processing_status }}
          </div>

          <template
            v-if="
              proposal.processing_status == 'With Assessor' ||
              proposal.processing_status == 'With Referral'
            "
          >
            <div class="card-body py-2 border-top">
              <div class="row">
                <div class="col-sm-12 top-buffer-s">
                  <div class="mb-2"><strong>Referrals</strong></div>
                  <div class="mb-3 mb-3">
                    <select
                      :disabled="!canLimitedAction"
                      ref="apiary_referral_groups"
                      class="form-select"
                    >
                      <option
                        v-for="group in apiaryReferralGroups"
                        :value="group.id"
                        :key="group.id"
                      >
                        {{ group.name }}
                      </option>
                    </select>
                    <template v-if="!sendingReferral">
                      <template v-if="selected_referral">
                        <label class="form-label float-start" for="Name"
                          >Comments</label
                        >
                        <textarea
                          class="form-control"
                          name="name"
                          v-model="referral_text"
                        ></textarea>
                        <a
                          v-if="canLimitedAction"
                          @click.prevent="sendReferral()"
                          class="actionBtn float-end"
                          >Send</a
                        >
                      </template>
                    </template>
                    <template v-else>
                      <span
                        v-if="canLimitedAction"
                        @click.prevent="sendReferral()"
                        disabled
                        class="actionBtn text-primary float-end"
                      >
                        Sending Referral&nbsp;
                        <i class="fa fa-circle-o-notch fa-spin fa-fw"></i>
                      </span>
                    </template>
                  </div>
                  <table class="table small-table table-hover table-referrals">
                    <thead>
                      <tr>
                        <th>Referral</th>
                        <th>Status/Action</th>
                      </tr>
                    </thead>
                    <tr v-for="r in proposal.latest_referrals" :key="r.id">
                      <td>
                        <small
                          ><strong>{{
                            r.apiary_referral.referral_group.name
                          }}</strong></small
                        ><br />
                        <small
                          ><strong>{{ formatDate(r.lodged_on) }}</strong></small
                        >
                      </td>
                      <td>
                        <small
                          ><strong>{{ r.processing_status }}</strong></small
                        ><br />
                        <template v-if="r.processing_status == 'Awaiting'">
                          <small v-if="canLimitedAction"
                            ><a @click.prevent="remindReferral(r)" href="#"
                              >Remind</a
                            >
                            /
                            <a @click.prevent="recallReferral(r)" href="#"
                              >Recall</a
                            ></small
                          >
                        </template>
                        <template v-else>
                          <small v-if="canLimitedAction"
                            ><a @click.prevent="resendReferral(r)" href="#"
                              >Resend</a
                            ></small
                          >
                        </template>
                      </td>
                    </tr>
                  </table>
                  <ApiaryReferralsForProposal
                    @refreshFromResponse="refreshFromResponse"
                    :proposal="proposal"
                    :canAction="canLimitedAction"
                    :isFinalised="isFinalised"
                    :referral_url="referralListURL"
                  />
                </div>
              </div>
            </div>
          </template>
          <div v-if="!isFinalised" class="card-body py-2 border-top">
            <div class="row">
              <div class="col-sm-12 top-buffer-s">
                <strong>Currently assigned to</strong><br />
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
                <div v-if="proposal.proposal_apiary">
                  <strong>Application</strong><br />
                  <a
                    class="actionBtn"
                    v-if="!showingProposal"
                    @click.prevent="toggleProposal()"
                    >Show Application</a
                  >
                  <a class="actionBtn" v-else @click.prevent="toggleProposal()"
                    >Hide Application</a
                  >
                </div>
                <div v-else>
                  <strong>Proposal</strong><br />
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
            </div>
          </template>
          <template
            v-if="proposal.processing_status == 'With Approver' || isFinalised"
          >
            <div class="card-body py-2 border-top">
              <div class="col-sm-12">
                <strong>Requirements</strong><br />
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
            <template
              v-if="
                proposal.processing_status == 'With Assessor' ||
                proposal.processing_status == 'With Referral'
              "
            >
              <div class="row">
                <div class="col-sm-12">
                  <div class="row mb-2"><strong>Action</strong><br /></div>
                </div>
                <div class="col-sm-12">
                  <button
                    style="width: 80%"
                    class="btn btn-primary"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="switchStatus('with_assessor_requirements')"
                  >
                    Enter Requirements</button
                  ><br />
                </div>
                <div class="col-sm-12">
                  <button
                    style="width: 80%"
                    class="btn btn-primary top-buffer-s"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="amendmentRequest()"
                  >
                    Request Amendment</button
                  ><br />
                </div>
                <div class="col-sm-12">
                  <button
                    style="width: 80%"
                    class="btn btn-primary top-buffer-s"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="proposedDecline()"
                  >
                    Propose to Decline
                  </button>
                </div>
              </div>
            </template>
            <template
              v-else-if="
                proposal.processing_status == 'With Assessor (Requirements)'
              "
            >
              <div class="row">
                <div class="col-sm-12">
                  <div class="row mb-2"><strong>Action</strong><br /></div>
                </div>
                <div class="col-sm-12">
                  <button
                    style="width: 80%"
                    class="btn btn-primary"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="switchStatus('with_assessor')"
                  >
                    Back To Processing</button
                  ><br />
                </div>
                <div class="col-sm-12" v-if="requirementsComplete">
                  <button
                    style="width: 80%"
                    class="btn btn-primary top-buffer-s"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="proposedApproval()"
                  >
                    Propose to Approve</button
                  ><br />
                </div>
              </div>
            </template>
            <template v-else-if="proposal.processing_status == 'With Approver'">
              <div class="row">
                <div class="col-sm-12">
                  <div class="row mb-2"><strong>Action</strong><br /></div>
                </div>
                <div class="col-sm-12">
                  <label class="form-label float-start" for="Name"
                    >Approver Comments</label
                  >
                  <textarea
                    class="form-control"
                    name="name"
                    v-model="approver_comment"
                  ></textarea
                  ><br />
                </div>
                <div class="col-sm-12" v-if="proposal.proposed_decline_status">
                  <button
                    style="width: 90%"
                    class="btn btn-primary"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="switchStatus('with_assessor')"
                  >
                    <!-- Back To Processing -->Back To Assessor</button
                  ><br />
                </div>
                <div class="col-sm-12" v-else>
                  <button
                    style="width: 90%"
                    class="btn btn-primary"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="switchStatus('with_assessor_requirements')"
                  >
                    <!-- Back To Requirements -->Back To Assessor</button
                  ><br />
                </div>
                <!-- v-if="!proposal.proposed_decline_status" -->
                <div class="col-sm-12">
                  <button
                    style="width: 90%"
                    class="btn btn-primary top-buffer-s"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="issueProposal()"
                  >
                    Approve</button
                  ><br />
                </div>
                <div class="col-sm-12">
                  <button
                    style="width: 90%"
                    class="btn btn-primary top-buffer-s"
                    :disabled="proposal.can_user_edit"
                    @click.prevent="declineProposal()"
                  >
                    Decline</button
                  ><br />
                </div>
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
              ref="approval_screen"
              @refreshFromResponse="refreshFromResponse"
            />
          </div>
          <div v-else>
            <ApprovalScreen
              :proposal="proposal"
              ref="approval_screen"
              @refreshFromResponse="refreshFromResponse"
            />
          </div>
        </template>
        <template
          v-if="
            (canLimitedAction &&
              proposal.processing_status == 'With Assessor (Requirements)') ||
            ((proposal.processing_status == 'With Approver' || isFinalised) &&
              showingRequirements)
          "
        >
          <div v-if="siteTransfer">
            <OriginatingApprovalRequirements
              :proposal="proposal"
              :originatingApprovalId="originatingApprovalId"
              :originatingApprovalLodgementNumber="
                originatingApprovalLodgementNumber
              "
            />
            <TargetApprovalRequirements
              :proposal="proposal"
              :targetApprovalId="targetApprovalId"
              :targetApprovalLodgementNumber="targetApprovalLodgementNumber"
            />
          </div>
          <div v-else>
            <Requirements
              :proposal="proposal"
              @refreshRequirements="refreshRequirements"
            />
          </div>
        </template>
        <!--template v-show="canSeeSubmission || (!canSeeSubmission && showingProposal)"-->
        <div v-show="canSeeProposal">
          <FormSection
            :formCollapse="false"
            label="Applicant"
            Index="applicant"
          >
            <div v-if="organisationApplicant">
              <form class="form-horizontal">
                <div class="row mb-3">
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
                <div class="row mb-3">
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
            </div>
            <div v-else>
              <form class="form-horizontal">
                <div class="row mb-3">
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
                <div class="row mb-3">
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
            </div>
          </FormSection>
          <FormSection
            :formCollapse="true"
            label="Address Details"
            Index="address_details"
          >
            <form class="form-horizontal">
              <div class="row mb-3">
                <label for="" class="col-sm-3 col-form-label">Street</label>
                <div class="col-sm-6">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="street"
                    placeholder=""
                    v-model="applicantAddressLine1"
                  />
                </div>
              </div>
              <div class="row mb-3">
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
                    v-model="applicantAddressLocality"
                  />
                </div>
              </div>
              <div class="row mb-3">
                <label for="" class="col-sm-3 col-form-label">State</label>
                <div class="col-sm-2">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="country"
                    placeholder=""
                    v-model="applicantAddressState"
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
                    v-model="applicantAddressPostcode"
                  />
                </div>
              </div>
              <div class="row mb-3">
                <label for="" class="col-sm-3 col-form-label">Country</label>
                <div class="col-sm-4">
                  <input
                    disabled
                    type="text"
                    class="form-control"
                    name="country"
                    v-model="applicantAddressCountry"
                  />
                </div>
              </div>
            </form>
          </FormSection>
          <FormSection
            :formCollapse="true"
            label="Contact Details"
            Index="contact_details"
          >
            <div v-if="organisationApplicant">
              test
              <table
                ref="contacts_datatable"
                :id="contacts_table_id"
                class="hover table border table-striped table-bordered dt-responsive pt-2"
                cellspacing="0"
                width="100%"
              ></table>
            </div>
            <div v-else>
              <form class="form-horizontal">
                <div class="row mb-3">
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
                <div class="row mb-3">
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
                <div class="row mb-3">
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
          <div class="col-md-12">
            <div class="row">
              <form
                :action="proposal_form_url"
                method="post"
                name="new_proposal"
                enctype="multipart/form-data"
              >
                <div v-if="proposal && proposal.application_type == 'Apiary'">
                  <ApiaryForm
                    v-if="proposal"
                    :proposal="proposal"
                    id="proposalStart"
                    ref="apiary_form"
                    :hasAssessorMode="hasAssessorMode"
                    :is_external="false"
                    :is_internal="true"
                    :show_col_vacant_when_submitted="true"
                  />
                </div>
                <div
                  v-else-if="
                    proposal && proposal.application_type == 'Site Transfer'
                  "
                >
                  <ApiarySiteTransfer
                    v-if="proposal"
                    :proposal="proposal"
                    id="proposalStart"
                    ref="site_transfer"
                    :hasAssessorMode="hasAssessorMode"
                    :is_external="false"
                    :is_internal="true"
                  />
                </div>

                <input
                  type="hidden"
                  name="csrfmiddlewaretoken"
                  :value="csrf_token"
                />
                <input
                  type="hidden"
                  name="schema"
                  :value="JSON.stringify(proposal)"
                />
                <input type="hidden" name="proposal_id" :value="1" />
                <div
                  v-if="hasAssessorMode"
                  class="navbar fixed-bottom"
                  style="background-color: #f5f5f5"
                >
                  <div v-if="hasAssessorMode" class="container">
                    <div class="row w-100 py-2">
                      <div class="col d-flex justify-content-end">
                        <button class="btn btn-primary" @click.prevent="save()">
                          Save Changes
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
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
      :is_apiary_proposal="isApiaryProposal"
      @refreshFromResponse="refreshFromResponse"
    />
    <ProposedApiaryIssuance
      ref="proposed_approval"
      :processing_status="proposal.processing_status"
      :proposal_apiary_id="apiaryProposal.id"
      :proposal_id="proposalId"
      :proposal="proposal"
      :proposal_type="proposal.proposal_type"
      :isApprovalLevelDocument="isApprovalLevelDocument"
      :submitter_email="proposal.submitter_email"
      :applicant_email="applicant_email"
      @refreshFromResponse="refreshFromResponse"
    />
  </div>
</template>
<script>
import { v4 as uuid } from "uuid";
import { markRaw } from "vue";
import ApiaryForm from "@/components/form_apiary.vue";
import ProposedDecline from "./proposal_proposed_decline.vue";
import AmendmentRequest from "./amendment_request.vue";
import Requirements from "./proposal_requirements.vue";
import OriginatingApprovalRequirements from "./originating_approval_requirements.vue";
import TargetApprovalRequirements from "./target_approval_requirements.vue";
import ProposedApiaryIssuance from "./proposed_apiary_issuance.vue";
import ApprovalScreen from "./proposal_approval.vue";
import ApprovalScreenSiteTransferTemporaryUse from "./proposal_approval_site_transfer_temporary_use.vue";
import CommsLogs from "@common-utils/comms_logs.vue";
import ApiaryReferralsForProposal from "@common-utils/apiary/apiary_referrals_for_proposal.vue";
import { api_endpoints, helpers, constants } from "@/utils/hooks";
import ApiarySiteTransfer from "@/components/form_apiary_site_transfer.vue";
import FormSection from "@/components/forms/section_toggle.vue";
import $ from "jquery";

export default {
  name: "InternalProposalApiary",
  data: function () {
    let vm = this;
    return {
      requirementsComplete: true,
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
      //department_users : [],
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
          url: "",
          dataSrc: "",
        },
        columns: [
          {
            title: "Name",
            mRender: function (data, type, full) {
              return full.first_name + " " + full.last_name;
            },
            defaultContent: "",
          },
          {
            title: "Phone",
            data: "phone_number",
            defaultContent: "",
          },
          {
            title: "Mobile",
            data: "mobile_number",
            defaultContent: "",
          },
          {
            title: "Fax",
            data: "fax_number",
            defaultContent: "",
          },
          {
            title: "Email",
            data: "email",
            defaultContent: "",
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
    // ProposalDisturbance,
    //ProposalApiary,
    ApiaryForm,
    ProposedDecline,
    AmendmentRequest,
    Requirements,
    OriginatingApprovalRequirements,
    TargetApprovalRequirements,
    ProposedApiaryIssuance,
    ApprovalScreen,
    ApprovalScreenSiteTransferTemporaryUse,
    CommsLogs,
    //MoreReferrals,
    ApiaryReferralsForProposal,

    //MapLocations,
    ApiarySiteTransfer,
    FormSection,
  },
  props: {
    proposalId: {
      type: Number,
    },
  },
  computed: {
    referralListURL: function () {
      return this.proposal != null
        ? helpers.add_endpoint_json(
            api_endpoints.apiary_referrals,
            "datatable_list",
          ) +
            "?proposal=" +
            this.proposal.id
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
    canSeeProposal: function () {
      return this.canSeeSubmission || this.showingProposal;
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
      return this.proposal && this.proposal.applicant.email
        ? this.proposal.applicant.email
        : "";
    },
    applicantAddress: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address;
      }
      return null;
    },
    applicantAddressLine1: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address.line1;
      }
      return "";
    },
    applicantAddressCountry: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address.country;
      }
      return "";
    },
    applicantAddressLocality: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address.locality;
      }
      return "";
    },
    applicantAddressState: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address.state;
      }
      return "";
    },
    applicantAddressPostcode: function () {
      if (this.proposal && this.proposal.applicant_address) {
        return this.proposal.applicant_address.postcode;
      }
      return "";
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
    isApiaryProposal: function () {
      let returnVal = false;
      if (this.proposal && this.proposal.proposal_apiary) {
        returnVal = true;
      }
      return returnVal;
    },
    apiaryProposal: function () {
      if (this.proposal && this.proposal.proposal_apiary) {
        return this.proposal.proposal_apiary;
      }
      return null;
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
    siteTransfer: function () {
      let returnVal = false;
      if (this.proposal.application_type === "Site Transfer") {
        returnVal = true;
      }
      return returnVal;
    },
    originatingApprovalId: function () {
      let returnVal = null;
      if (this.proposal.application_type === "Site Transfer") {
        returnVal = this.proposal.proposal_apiary.originating_approval_id;
      }
      return returnVal;
    },
    originatingApprovalLodgementNumber: function () {
      let returnVal = null;
      if (this.proposal.application_type === "Site Transfer") {
        returnVal =
          this.proposal.proposal_apiary.originating_approval_lodgement_number;
      }
      return returnVal;
    },
    targetApprovalId: function () {
      let returnVal = null;
      if (this.proposal.application_type === "Site Transfer") {
        returnVal = this.proposal.proposal_apiary.target_approval_id;
      }
      return returnVal;
    },
    targetApprovalLodgementNumber: function () {
      let returnVal = "";
      if (this.proposal.application_type === "Site Transfer") {
        returnVal =
          this.proposal.proposal_apiary.target_approval_lodgement_number;
      }
      return returnVal;
    },
  },
  methods: {
    formatDate: function (data) {
      return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
    },
    refreshRequirements: function (bool) {
      let vm = this;
      vm.requirementsComplete = bool;
    },
    locationUpdated: function () {
      console.log("in locationUpdated()");
    },
    checkAssessorData: function () {
      //check assessor boxes and clear value of hidden assessor boxes so it won't get printed on approval pdf.

      //select all fields including hidden fields
      var all_fields = $(
        "input[type=text]:required, textarea:required, input[type=checkbox]:required, input[type=radio]:required, input[type=file]:required, select:required",
      );

      all_fields.each(function () {
        var ele = $("[name=" + this.name + "-Assessor]");
        if (ele.length > 0) {
          var visiblity = $("[name=" + this.name + "-Assessor]").is(":visible");
          if (!visiblity) {
            if (ele[0].value != "") {
              ele[0].value = "";
            }
          }
        }
      });
    },
    initialiseOrgContactTable: function () {
      let vm = this;
      if (vm.proposal && !vm.contacts_table_initialised) {
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
    proposedDecline: function () {
      this.save_wo();
      this.$refs.proposed_decline.decline =
        this.proposal.proposaldeclineddetails != null
          ? helpers.copyObject(this.proposal.proposaldeclineddetails)
          : {};
      this.$refs.proposed_decline.isModalOpen = true;
    },
    proposedApproval: function () {
      let copiedProposedIssuanceApproval = helpers.copyObject(
        this.proposal.proposed_issuance_approval,
      );
      if (
        copiedProposedIssuanceApproval != null &&
        this.proposal.proposal_type == "Renewal"
      ) {
        copiedProposedIssuanceApproval.expiry_date = null;
        copiedProposedIssuanceApproval.start_date = null;
      }
      this.$refs.proposed_approval.approval =
        this.proposal.proposed_issuance_approval != null
          ? copiedProposedIssuanceApproval
          : {};
      if (this.proposal.proposed_issuance_approval == null) {
        var test_approval = {
          cc_email: this.proposal.referral_email_list,
        };
        this.$refs.proposed_approval.approval =
          helpers.copyObject(test_approval);
        // this.$refs.proposed_approval.$refs.bcc_email=this.proposal.referral_email_list;
      }
      //this.$refs.proposed_approval.submitter_email=helpers.copyObject(this.proposal.submitter_email);
      // if(this.proposal.applicant.email){
      //     this.$refs.proposed_approval.applicant_email=helpers.copyObject(this.proposal.applicant.email);
      // }
      this.$refs.proposed_approval.isModalOpen = true;
      // Force to refresh the map to display it in case it is not shown.
      // When the map is in modal, it is often not shown unless the map is resized
      this.$refs.proposed_approval.forceToRefreshMap();
    },
    issueProposal: function () {
      if (
        this.isApprovalLevelDocument &&
        this.proposal.approval_level_comment == ""
      ) {
        swal.fire({
          title: "Error",
          text: "Please add Approval document or comments before final approval",
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
        });
      } else {
        this.$refs.proposed_approval.approval =
          this.proposal.proposed_issuance_approval != null
            ? helpers.copyObject(this.proposal.proposed_issuance_approval)
            : {};
        this.$refs.proposed_approval.approval.start_date = moment(
          this.$refs.proposed_approval.approval.start_date,
          "DD/MM/YYYY",
        ).format("YYYY-MM-DD");
        this.$refs.proposed_approval.approval.expiry_date = moment(
          this.$refs.proposed_approval.approval.expiry_date,
          "DD/MM/YYYY",
        ).format("YYYY-MM-DD");
        this.$refs.proposed_approval.state = "final_approval";
        this.$refs.proposed_approval.isModalOpen = true;

        // Force to refresh the map to display it in case it is not shown.
        // When the map is in modal, it is often not shown unless the map is resized
        this.$refs.proposed_approval.forceToRefreshMap();
      }
    },
    declineProposal: function () {
      this.$refs.proposed_decline.decline =
        this.proposal.proposaldeclineddetails != null
          ? helpers.copyObject(this.proposal.proposaldeclineddetails)
          : {};
      this.$refs.proposed_decline.isModalOpen = true;
    },
    amendmentRequest: function () {
      this.save_wo();
      let values = "";
      $(".deficiency").each((i, d) => {
        values +=
          $(d).val() != ""
            ? `Question - ${$(d).data("question")}\nDeficiency - ${$(d).val()}\n\n`
            : "";
      });
      //this.deficientFields();
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
        }
      });
      vm.highlight_deficient_fields(deficient_fields);
    },
    save: function () {
      let vm = this;
      vm.checkAssessorData();
      let formData = new FormData(
        document.querySelector('form[name="new_proposal"]'),
      );
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
    save_wo: function () {
      let vm = this;
      vm.checkAssessorData();
      let formData = new FormData(
        document.querySelector('form[name="new_proposal"]'),
      );
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
          // No success action needed
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
      if (vm.$refs.approval_screen) {
        vm.$refs.approval_screen.updateComponentSiteSelectionKey();
      }
    },
    assignTo: function () {
      let vm = this;
      let unassign;
      let data = {};
      if (vm.processing_status == "With Approver") {
        unassign =
          vm.proposal.assigned_approver != null &&
          vm.proposal.assigned_approver != "undefined"
            ? false
            : true;
        data = { assessor_id: vm.proposal.assigned_approver };
      } else {
        unassign =
          vm.proposal.assigned_officer != null &&
          vm.proposal.assigned_officer != "undefined"
            ? false
            : true;
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
    switchStatus: function (status) {
      let vm = this;
      //vm.save_wo();
      //let vm = this;
      if (
        vm.proposal.processing_status == "With Assessor" &&
        status == "with_assessor_requirements"
      ) {
        vm.checkAssessorData();
        let formData = new FormData(
          document.querySelector('form[name="new_proposal"]'),
        );
        // First POST: Save proposal form
        fetch(vm.proposal_form_url, {
          method: "POST",
          body: formData,
        })
          .then(() => {
            // Second POST: Switch status after saving
            const data = {
              status: status,
              approver_comment: vm.approver_comment,
            };

            fetch(
              helpers.add_endpoint_json(
                api_endpoints.proposals,
                vm.proposal.id + "/switch_status",
              ),
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/x-www-form-urlencoded", // emulateJSON
                },
                body: new URLSearchParams(data),
              },
            )
              .then((response) => response.json())
              .then((response) => {
                vm.proposal = response;
                vm.original_proposal = helpers.copyObject(response);
                vm.proposal.applicant.address =
                  vm.proposal.applicant.address != null
                    ? vm.proposal.applicant.address
                    : {};
                vm.approver_comment = "";

                vm.$nextTick(() => {
                  vm.initialiseAssignedOfficerSelect(true);
                  vm.updateAssignedOfficerSelect();
                });
              })
              .catch((error) => {
                vm.proposal = helpers.copyObject(vm.original_proposal);
                vm.proposal.applicant.address =
                  vm.proposal.applicant.address != null
                    ? vm.proposal.applicant.address
                    : {};
                swal.fire({
                  title: "Proposal Error",
                  //text: helpers.apiVueResourceError(error),
                  text: error,
                  icon: "error",
                  customClass: {
                    confirmButton: "btn btn-primary",
                  },
                });
              });
          })
          .catch((error) => {
            console.log("Error saving proposal form:", error);
          });
      }

      //if approver is pushing back proposal to Assessor then navigate the approver back to dashboard page
      if (
        vm.proposal.processing_status == "With Approver" &&
        (status == "with_assessor_requirements" || status == "with_assessor")
      ) {
        let data = { status: status, approver_comment: vm.approver_comment };

        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposals,
            vm.proposal.id + "/switch_status",
          ),
          {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded", // emulateJSON
            },
            body: new URLSearchParams(data),
          },
        )
          .then((response) => response.json())
          .then((response) => {
            vm.proposal = response;
            vm.original_proposal = helpers.copyObject(response);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            vm.approver_comment = "";

            vm.$nextTick(() => {
              vm.initialiseAssignedOfficerSelect(true);
              vm.updateAssignedOfficerSelect();
            });

            vm.$router.push({ path: "/internal" });
          })
          .catch((error) => {
            vm.proposal = helpers.copyObject(vm.original_proposal);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            swal.fire({
              title: "Proposal Error",
              //text: helpers.apiVueResourceError(error),
              text: error,
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
          });
      } else {
        let data = { status: status, approver_comment: vm.approver_comment };
        fetch(
          helpers.add_endpoint_json(
            api_endpoints.proposals,
            vm.proposal.id + "/switch_status",
          ),
          {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams(data),
          },
        )
          .then((response) => response.json())
          .then((response) => {
            vm.proposal = response;
            vm.original_proposal = helpers.copyObject(response);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            vm.approver_comment = "";

            vm.$nextTick(() => {
              vm.initialiseAssignedOfficerSelect(true);
              vm.updateAssignedOfficerSelect();
            });
          })
          .catch((error) => {
            vm.proposal = helpers.copyObject(vm.original_proposal);
            vm.proposal.applicant.address =
              vm.proposal.applicant.address != null
                ? vm.proposal.applicant.address
                : {};
            swal.fire({
              title: "Proposal Error",
              //text: helpers.apiVueResourceError(error),
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
      fetch("/api/apiary_referral_groups/get_referral_group_list/")
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
    sendReferral: function () {
      let vm = this;
      //vm.save_wo();
      vm.checkAssessorData();
      let formData = new FormData(
        document.querySelector('form[name="new_proposal"]'),
      );
      vm.sendingReferral = true;
      // First POST: Save proposal form
      fetch(vm.proposal_form_url, {
        method: "POST",
        body: formData,
      })
        .then(() => {
          // Second POST: Send referral

          let data = { group_id: vm.selected_referral, text: vm.referral_text };
          //vm.sendingReferral = true;
          // need to create Referral, ApiaryReferral at this point
          let url = helpers.add_endpoint_json(
            api_endpoints.proposal_apiary,
            vm.proposal.proposal_apiary.id + "/apiary_assessor_send_referral",
          );
          fetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded", // emulateJSON
            },
            body: new URLSearchParams(data),
          })
            .then((response) => response.json())
            .then((response) => {
              vm.sendingReferral = false;
              vm.original_proposal = helpers.copyObject(response);
              vm.proposal = response;
              //vm.proposal.applicant.address = vm.proposal.applicant.address != null ? vm.proposal.applicant.address : {};
              vm.proposal.relevant_applicant_address =
                vm.proposal.relevant_applicant_address != null
                  ? vm.proposal.relevant_applicant_address
                  : {};
              swal.fire({
                title: "Referral Sent",
                text:
                  "The referral has been sent to " +
                  vm.apiaryReferralGroups.find(
                    (d) => d.id == vm.selected_referral,
                  ).name,
                icon: "success",
                customClass: {
                  confirmButton: "btn btn-primary",
                },
              });
              $(vm.$refs.apiaryReferralGroups).val(null).trigger("change");
              vm.selected_referral = "";
              vm.referral_text = "";
            })
            .catch((error) => {
              console.log(error);
              swal.fire({
                title: "Referral Error",
                //text: helpers.apiVueResourceError(error),
                text: error,
                icon: "error",
                customClass: {
                  confirmButton: "btn btn-primary",
                },
              });
              vm.sendingReferral = false;
            });
        })
        .catch((err) => {
          console.log(err);
        });
    },
    remindReferral: function (r) {
      let vm = this;

      fetch(
        helpers.add_endpoint_json(
          api_endpoints.apiary_referrals,
          r.apiary_referral.id + "/remind",
        ),
      )
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const data = await response.json();
          vm.original_proposal = helpers.copyObject(data);
          vm.proposal = data;
          vm.proposal.applicant.address =
            vm.proposal.applicant.address != null
              ? vm.proposal.applicant.address
              : {};
          swal.fire({
            title: "Referral Reminder",
            text:
              "A reminder has been sent to " +
              r.apiary_referral.referral_group.name,
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        })
        .catch((error) => {
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
    resendReferral: function (r) {
      let vm = this;

      fetch(
        helpers.add_endpoint_json(
          api_endpoints.apiary_referrals,
          r.apiary_referral.id + "/resend",
        ),
      )
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const data = await response.json();
          vm.original_proposal = helpers.copyObject(data);
          vm.proposal = data;
          vm.proposal.applicant.address =
            vm.proposal.applicant.address != null
              ? vm.proposal.applicant.address
              : {};
          swal.fire({
            title: "Referral Resent",
            text:
              "The referral has been resent to " +
              r.apiary_referral.referral_group.name,
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        })
        .catch((error) => {
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
    recallReferral: function (r) {
      let vm = this;
      fetch(
        helpers.add_endpoint_json(
          api_endpoints.apiary_referrals,
          r.apiary_referral.id + "/recall",
        ),
      )
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          const data = await response.json();
          vm.original_proposal = helpers.copyObject(data);
          vm.proposal = data;
          vm.proposal.applicant.address =
            vm.proposal.applicant.address != null
              ? vm.proposal.applicant.address
              : {};
          swal.fire({
            title: "Referral Recall",
            text:
              "The referral has been recalled from " +
              r.apiary_referral.referral_group.name,
            icon: "success",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        })
        .catch((error) => {
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
  },
  mounted: async function () {
    await this.fetchApiaryReferralGroups();
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
    this.$nextTick(async () => {
      if (this.organisationApplicant) {
        await this.initialiseOrgContactTable();
      }
      vm.initialiseSelects();
      vm.form = markRaw(document.forms.new_proposal);
      if (vm.hasAmendmentRequest) {
        vm.deficientFields();
      }
    });
  },
  created: async function () {
    try {
      fetch(`/api/proposal/${this.proposalId}/internal_proposal.json`)
        .then(async (res) => {
          if (!res.ok) {
            return res.json().then((err) => {
              throw err;
            });
          }
          const data = await res.json();
          this.proposal = Object.assign({}, data);

          if (this.proposal.applicant && this.proposal.applicant.address) {
            this.proposal.applicant.address =
              this.proposal.applicant.address != null
                ? this.proposal.applicant.address
                : {};
          }
          this.hasAmendmentRequest = this.proposal.hasAmendmentRequest;
        })
        .catch((err) => {
          console.log(err);
        });
    } catch (err) {
      console.log(err);
    }
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
