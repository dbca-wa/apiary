<template>
  <div class="container" id="userInfo">
    <div class="row">
      <div class="col-sm-12">
        <FormSection
          :form-collapse="false"
          label="Organisations"
          subtitle="Link to the Organisations you are an employee of and for which you are managing licences"
          class="mt-3"
        >
          <div class="card m-1 p-3">
            <form class="form-horizontal" name="orgForm" method="post">
              <div class="mb-3">
                <label
                  for=""
                  class="col-sm-6 col-form-label fw-normal fs-5 pb-3"
                  >Do you manage licences on behalf of an organisation?</label
                >
                <div class="col-sm-4">
                  <div class="form-check form-check-inline">
                    <input
                      :disabled="hasOrgs"
                      type="radio"
                      name="behalf_of_org"
                      class="form-check-input"
                      v-model="managesOrg"
                      value="No"
                    />
                    <label class="form-check-label fw-normal">No</label>
                  </div>
                  <div class="form-check form-check-inline">
                    <input
                      type="radio"
                      name="behalf_of_org"
                      v-model="managesOrg"
                      value="Yes"
                      class="form-check-input"
                    />
                    <label class="form-check-label fw-normal">Yes</label>
                  </div>
                  <div class="form-check form-check-inline">
                    <label class="radio-inline">
                      <input
                        type="radio"
                        name="behalf_of_org"
                        v-model="managesOrg"
                        value="Consultant"
                        class="form-check-input"
                      />
                      <label class="form-check-label fw-normal"
                        >Yes, as a consultant</label
                      >
                    </label>
                  </div>
                </div>
                <div v-if="managesOrg == 'Yes'">
                  <div class="col-sm-3">
                    <button
                      class="btn btn-primary"
                      v-if="hasOrgs && !addingCompany"
                      @click.prevent="addCompany()"
                    >
                      Add Another Organisation
                    </button>
                  </div>
                </div>
              </div>
              <div
                v-if="
                  current_user.disturbance_organisations &&
                  current_user.disturbance_organisations.length > 0
                "
              >
                <hr class="mt-3" />
                <h4 class="mb-3 mt-3">Linked Organisations</h4>
              </div>
              <div
                v-for="org in current_user.disturbance_organisations"
                v-bind:key="org.id"
              >
                <div class="card p-3 mb-3 w-50">
                  <label for="" class="form-label">Organisation</label>
                  <div class="mb-3">
                    <input
                      ref="organisation"
                      type="text"
                      disabled
                      class="form-control"
                      name="organisation"
                      v-model="org.name"
                      placeholder=""
                      required
                    />
                  </div>
                  <label for="" class="form-label">ABN/ACN</label>
                  <div class="mb-3">
                    <input
                      ref="abn"
                      type="text"
                      disabled
                      class="form-control"
                      name="abn"
                      v-model="org.abn"
                      placeholder=""
                      required
                    />
                  </div>
                  <div>
                    <button
                      class="btn btn-danger"
                      @click.prevent="unlinkUser(org)"
                    >
                      <i class="fa fa-chain-broken me-2"></i>Unlink
                    </button>
                  </div>
                </div>
              </div>
              <div
                v-if="orgRequest_pending && orgRequest_pending.length > 0"
                class="mb-3"
              >
                <h4>Organisation Requests Pending</h4>
              </div>
              <div v-for="orgReq in orgRequest_pending" v-bind:key="orgReq.id">
                <div class="card border rounded w-50 p-3 mb-3">
                  <label for="" class="form-label">Organisation</label>
                  <div class="mb-3">
                    <input
                      ref="organisation"
                      type="text"
                      disabled
                      class="form-control"
                      name="organisation"
                      v-model="orgReq.name"
                      placeholder="My Organisation Pty Ltd"
                    />
                  </div>
                  <label for="" class="form-label">ABN/ACN</label>
                  <div class="mb-3">
                    <input
                      type="text"
                      disabled
                      class="form-control"
                      ref="abn"
                      name="abn"
                      v-model="orgReq.abn"
                      placeholder="XXXXXXXXXXX"
                    />
                  </div>
                  <div>
                    <span class="badge bg-secondary p-3">
                      <i class="bi bi-hourglass-split"></i> Pending Approval
                    </span>
                  </div>
                </div>
              </div>
              <div
                v-for="orgReq in orgRequest_amendment_requested"
                v-bind:key="orgReq.id"
              >
                <div class="mb-3">
                  <label for="" class="col-sm-2 col-form-label"
                    >Organisation</label
                  >
                  <div class="col-sm-3">
                    <input
                      type="text"
                      disabled
                      class="form-control"
                      ref="organisation"
                      name="organisation"
                      v-model="orgReq.name"
                      placeholder=""
                    />
                  </div>
                  <label for="" class="col-sm-1 col-form-label">ABN/ACN</label>
                  <div class="col-sm-3">
                    <input
                      type="text"
                      disabled
                      class="form-control"
                      name="abn"
                      ref="abn"
                      v-model="orgReq.abn"
                      placeholder=""
                    />
                  </div>
                  <span class="btn btn-primary btn-file float-start">
                    Upload New File
                    <input
                      type="file"
                      ref="uploadedFile"
                      @change="uploadNewFileUpdateOrgRequest(orgReq)"
                    />
                  </span>
                  <span
                    class="float-start"
                    style="margin-left: 10px; margin-top: 10px"
                    >{{ uploadedFileName }}</span
                  >
                </div>
              </div>

              <div
                v-if="managesOrg == 'Consultant' && addingCompany"
                class="container border rounded p-3 mb-3"
              >
                <h4>New Organisation (as consultant)</h4>
                <div class="row mb-3">
                  <div class="col-sm-6">
                    <label for="" class="form-label"
                      >Organisation <span class="text-danger">*</span></label
                    >
                    <input
                      ref="organisation"
                      type="text"
                      class="form-control"
                      name="organisation"
                      v-model="newOrg.name"
                      placeholder="My Organisation Pty Ltd"
                    />
                  </div>
                </div>
                <div class="mb-3">
                  <div class="col-sm-6">
                    <label for="" class="col-sm-2 col-form-label"
                      >ABN/ACN <span class="text-danger">*</span></label
                    >
                    <input
                      ref="abn"
                      type="text"
                      class="form-control"
                      name="abn"
                      v-model="newOrg.abn"
                      placeholder="XXXXXXXXXXX"
                    />
                  </div>
                  <div class="col-sm-2">
                    <button
                      v-if="newOrg.detailsChecked"
                      @click.prevent="checkOrganisation()"
                      class="btn btn-primary"
                    >
                      Check Details
                    </button>
                  </div>
                </div>
                <div class="mb-3">
                  <p>
                    Please upload a letter with an organisation letterhead
                    stating that you are a consultant for the organisation.
                  </p>

                  <div class="mb-3">
                    <span class="btn btn-primary btn-file">
                      Attach File
                      <input
                        type="file"
                        ref="uploadedFile"
                        @change="readFile()"
                      />
                    </span>
                    <span style="margin-left: 10px; margin-top: 10px">{{
                      uploadedFileName
                    }}</span>
                  </div>

                  <p>
                    You will be notified by email once the Department has
                    checked the organisation details.
                  </p>

                  <div class="clearfix">
                    <button
                      v-if="!registeringOrg"
                      @click.prevent="orgConsultRequest()"
                      class="btn btn-primary float-end"
                    >
                      Submit
                    </button>
                    <button v-else disabled class="btn btn-primary float-end">
                      <i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting
                    </button>
                  </div>
                </div>
              </div>

              <div
                v-if="managesOrg == 'Yes' && addingCompany"
                class="container border rounded p-3 mb-3"
              >
                <h4>New Organisation</h4>
                <div class="row mb-3">
                  <div class="col-sm-6">
                    <label for="" class="col-sm-3 col-form-label"
                      >Organisation <span class="text-danger">*</span></label
                    >
                    <input
                      ref="organisation"
                      type="text"
                      class="form-control"
                      name="organisation"
                      v-model="newOrg.name"
                      placeholder="My Organisation Pty Ltd"
                    />
                  </div>
                </div>
                <div class="row mb-3">
                  <div class="col-sm-6">
                    <label for="" class="col-sm-3 col-form-label"
                      >ABN/ACN <span class="text-danger">*</span></label
                    >
                    <input
                      ref="abn"
                      type="text"
                      class="form-control"
                      name="abn"
                      v-model="newOrg.abn"
                      placeholder="XXXXXXXXXXX"
                    />
                  </div>
                </div>
                <div class="row mb-3">
                  <div class="col-sm-3">
                    <button
                      @click.prevent="checkOrganisation()"
                      class="btn btn-primary"
                    >
                      Check Details
                    </button>
                  </div>
                </div>
                <div class="mb-3" v-if="newOrg.exists && newOrg.detailsChecked">
                  <hr />
                  <p>
                    This organisation has already been registered with the
                    system.
                  </p>
                  <p>Please enter the two pin codes below.</p>
                  <p>
                    These pin codes can be retrieved from one of the following
                    people:
                  </p>
                  <p>
                    <span
                      v-for="name in newOrg.first_five.split(',')"
                      class="badge bg-secondary me-2 p-2"
                      :key="name"
                      >{{ name }}</span
                    >
                  </p>
                  <hr />
                  <div class="col-sm-3">
                    <label for="" class="form-label fw-normal"
                      >Pin 1 <span class="text-danger">*</span></label
                    >
                    <div class="mb-3">
                      <input
                        ref="pin1"
                        type="text"
                        class="form-control"
                        name="pin1"
                        v-model="newOrg.pin1"
                        placeholder=""
                      />
                    </div>
                  </div>
                  <div class="col-sm-3">
                    <label for="" class="form-label fw-normal"
                      >Pin 2 <span class="text-danger">*</span></label
                    >
                    <div class="mb-3">
                      <input
                        ref="pin2"
                        type="text"
                        class="form-control"
                        name="pin2"
                        v-model="newOrg.pin2"
                        placeholder=""
                      />
                    </div>
                  </div>
                  <div class="clearfix mb-3">
                    <button
                      v-if="!validatingPins"
                      @click.prevent="validatePins()"
                      class="btn btn-primary float-start"
                    >
                      Validate
                    </button>
                    <button v-else class="btn btn-primary float-start">
                      <i class="fa fa-spin fa-spinner"></i>&nbsp;Validating Pins
                    </button>
                  </div>
                </div>
                <div
                  class="mb-3"
                  v-else-if="!newOrg.exists && newOrg.detailsChecked"
                >
                  <hr />
                  <p>
                    This organisation has not yet been registered with this
                    system.
                  </p>
                  <p>
                    Please upload a letter with an organisation letterhead
                    stating that you are an employee of this organisation.
                  </p>
                  <div class="mb-3">
                    <span class="btn btn-primary btn-file me-2">
                      Attach File<i class="bi bi-upload ms-2"></i>
                      <input
                        type="file"
                        ref="uploadedFile"
                        @change="readFile()"
                      />
                    </span>
                    <span>{{ uploadedFileName }}</span>
                  </div>
                  <div>
                    <p>
                      You will be notified by email once the Department has
                      checked the organisation details.
                    </p>
                  </div>

                  <div class="clearfix">
                    <button
                      v-if="!registeringOrg"
                      @click.prevent="orgRequest()"
                      class="btn btn-primary float-end"
                    >
                      Submit
                    </button>
                    <button v-else disabled class="btn btn-primary float-end">
                      <i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting
                    </button>
                  </div>
                </div>
                <div
                  class="mb-3"
                  v-else-if="newOrg.exists && !newOrg.detailsChecked"
                >
                  <p>
                    Please upload a letter with an organisation letterhead
                    stating that you are an employee of this organisation.<br />
                  </p>
                  <div class="clearfix mb-3">
                    <span class="btn btn-primary btn-file float-start">
                      Attach File
                      <input
                        type="file"
                        ref="uploadedFile"
                        @change="readFile()"
                      />
                    </span>
                    <span
                      class="float-start"
                      style="margin-left: 10px; margin-top: 10px"
                      >{{ uploadedFileName }}</span
                    >
                  </div>
                  <label
                    for=""
                    class="col-sm-10 col-form-label"
                    style="text-align: left"
                    >You will be notified by email once the Department has
                    checked the organisation details.</label
                  >
                  <div class="col-sm-12">
                    <button
                      v-if="!registeringOrg"
                      @click.prevent="orgRequest()"
                      class="btn btn-primary float-end"
                    >
                      Submit
                    </button>
                    <button v-else disabled class="btn btn-primary float-end">
                      <i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>
        </FormSection>
      </div>
    </div>
  </div>
</template>

<script>
import { v4 as uuid } from "uuid";
import $ from "jquery";
import { api_endpoints, helpers, fetch_util } from "@/utils/hooks";
import { parseFetchError } from "@/utils/helpers";
import FormSection from "@/components/forms/section_toggle.vue";

export default {
  name: "MyUserDetails",
  components: {
    FormSection,
    // SecureBaseLink,
  },
  data() {
    return {
      oBody: "oBody" + uuid(),
      current_user: {
        disturbance_organisations: [],
      },
      newOrg: {
        name: "",
        abn: "",
        detailsChecked: false,
        exists: false,
      },
      loading: [],
      registeringOrg: false,
      validatingPins: false,
      addingCompany: false,
      managesOrg: "No",
      managesOrgConsultant: "No",
      uploadedFile: null,
      uploadedID: null,

      updatingPersonal: false,
      updatingAddress: false,
      updatingContact: false,
      role: null,
      orgRequest_pending: [],
      orgRequest_amendment_requested: [],
      new_user: false,
      datepickerOptions: {
        format: "YYYY-MM-DD",
        showClear: true,
        useCurrent: false,
        keepInvalid: true,
        allowInputToggle: true,
      },
      showCompleteMsg: false,
    };
  },
  watch: {
    managesOrg: function () {
      if (this.managesOrg == "Yes") {
        this.newOrg.detailsChecked = false;
        this.role = "employee";
      } else if (this.managesOrg == "Consultant") {
        this.newOrg.detailsChecked = false;
        this.role = "consultant";
      } else {
        this.role = null;
        this.newOrg.detailsChecked = false;
      }

      if (this.managesOrg == "Yes" && !this.hasOrgs && this.newOrg) {
        this.addCompany();
      } else if (this.managesOrg == "No" && this.newOrg) {
        this.resetNewOrg();
        this.uploadedFile = null;
        this.addingCompany = false;
      } else if (this.managesOrg == "Consultant" && this.newOrg) {
        this.addCompany();
      } else {
        this.addCompany();
        this.addingCompany = false;
      }
    },
  },
  computed: {
    hasOrgs: function () {
      if (this.current_user) {
        return this.current_user.disturbance_organisations &&
          this.current_user.disturbance_organisations.length > 0
          ? true
          : false;
      }
      return false;
    },
    uploadedFileName: function () {
      return this.uploadedFile != null ? this.uploadedFile.name : "";
    },
  },
  methods: {
    readFile: function () {
      let vm = this;
      let _file = null;
      var input = $(vm.$refs.uploadedFile)[0];
      if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.readAsDataURL(input.files[0]);
        reader.onload = function (e) {
          _file = e.target.result;
        };
        _file = input.files[0];
      }
      vm.uploadedFile = _file;
    },
    readFileID: async function () {
      let vm = this;
      let _file = null;
      var input = $(vm.$refs.uploadedID)[0];
      if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.readAsDataURL(input.files[0]);
        reader.onload = function (e) {
          _file = e.target.result;
        };
        _file = input.files[0];
      }
      vm.uploadedID = _file;
      await vm.uploadID();
    },
    addCompany: function () {
      this.newOrg.push = {
        name: "",
        abn: "",
      };
      this.addingCompany = true;
      this.$nextTick(() => {
        if (this.managesOrg == "Yes") {
          this.$refs.organisation?.focus();
        }
        if (this.managesOrg == "Consultant") {
          this.$refs.organisation?.focus();
        }
      });
    },
    resetNewOrg: function () {
      this.newOrg = {
        detailsChecked: false,
        exists: false,
      };
    },
    checkOrganisation: function () {
      console.log("Entered CheckOrg");
      let vm = this;
      let new_organisation = vm.newOrg;
      for (var organisation in vm.current_user.disturbance_organisations) {
        if (
          new_organisation.abn &&
          vm.current_user.disturbance_organisations[organisation].abn ==
            new_organisation.abn
        ) {
          swal.fire({
            title: "Checking Organisation",
            text: "You are already associated with this organisation.",
            icon: "info",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
          vm.registeringOrg = false;
          vm.uploadedFile = null;
          vm.addingCompany = false;
          vm.resetNewOrg();
          return;
        }
      }

      if (!this.newOrg.name) {
        this.$refs.organisation?.focus();
        return;
      }

      if (!this.newOrg.abn) {
        this.$refs.abn?.focus();
        return;
      }

      let request = fetch_util.fetchUrl(
        helpers.add_endpoint_json(api_endpoints.organisations, "existence"),
        { method: "POST", body: JSON.stringify(this.newOrg) },
        {
          emulateJSON: true,
        },
      );
      request.then(
        (response) => {
          this.newOrg.exists = response.exists;
          this.newOrg.id = response.id;
          this.newOrg.detailsChecked = false;
          if (response.first_five) {
            this.newOrg.first_five = response.first_five;
            this.newOrg.detailsChecked = true;
          }
          this.newOrg.detailsChecked = this.newOrg.exists
            ? this.newOrg.detailsChecked
            : true;
          if (this.newOrg.detailsChecked && this.newOrg.exists) {
            this.$nextTick(() => {
              this.$refs.pin1?.focus();
            });
          }
        },
        async (error) => {
          this.newOrg.detailsChecked = false;
          const errorMessage = await parseFetchError(error);
          swal.fire({
            title: "Checking Organisation",
            text:
              "There was an error checking this organisation." + errorMessage,
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        },
      );
    },
    validatePins: function () {
      let vm = this;
      vm.validatingPins = true;

      if (!this.newOrg.pin1) {
        this.$refs.pin1?.focus();
        vm.validatingPins = false;
        return;
      }

      if (!this.newOrg.pin2) {
        this.$refs.pin2?.focus();
        vm.validatingPins = false;
        return;
      }

      let request = fetch_util.fetchUrl(
        helpers.add_endpoint_json(
          api_endpoints.organisations,
          vm.newOrg.id + "/validate_pins",
        ),
        { method: "POST", body: JSON.stringify(this.newOrg) },
        {
          emulateJSON: true,
        },
      );
      request.then(
        (response) => {
          if (response.valid) {
            swal.fire({
              title: "Validate Pins",
              text: "The pins you entered have been validated and your request will be processed by Organisation Administrator.",
              icon: "success",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
            vm.registeringOrg = false;
            vm.uploadedFile = null;
            vm.addingCompany = false;
            vm.resetNewOrg();

            let request = fetch_util.fetchUrl(api_endpoints.my_user_details);
            request
              .then((response) => {
                vm.current_user = response;
                if (
                  vm.current_user.disturbance_organisations &&
                  vm.current_user.disturbance_organisations.length > 0
                ) {
                  vm.managesOrg = "Yes";
                }
              })
              .catch((error) => {
                console.log(error);
              });
          } else {
            swal.fire({
              title: "Validate Pins",
              text: "The pins you entered were incorrect",
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
          }
          vm.validatingPins = false;
        },
        (error) => {
          console.log(error);
          vm.validatingPins = false;
        },
      );
    },
    orgRequest: function () {
      let vm = this;
      vm.registeringOrg = true;
      let data = new FormData();
      data.append("name", vm.newOrg.name);
      data.append("abn", vm.newOrg.abn);
      data.append("identification", vm.uploadedFile);
      data.append("role", vm.role);
      vm.newOrg.name = vm.newOrg.name == null ? "" : vm.newOrg.name;
      vm.newOrg.abn = vm.newOrg.abn == null ? "" : vm.newOrg.abn;
      if (
        vm.newOrg.name == "" ||
        vm.newOrg.abn == "" ||
        vm.uploadedFile == null
      ) {
        vm.registeringOrg = false;
        swal.fire({
          title: "Error submitting organisation request",
          text: "Please enter the organisation details and attach a file before submitting your request.",
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
        });
      } else {
        console.log(data);
        let request = fetch_util.fetchUrl(
          api_endpoints.organisation_requests,
          { method: "POST", body: data },
          {},
        );
        request.then(
          () => {
            vm.registeringOrg = false;
            vm.uploadedFile = null;
            vm.addingCompany = false;
            vm.resetNewOrg();
            swal
              .fire({
                title: "Sent",
                html: "Your organisation request has been successfully submitted.",
                icon: "success",
                customClass: {
                  confirmButton: "btn btn-primary",
                },
              })
              .then(() => {
                if (this.$route.name == "account") {
                  window.location.reload(true);
                }
              });
          },
          async (error) => {
            vm.registeringOrg = false;
            swal.fire({
              title: "Error submitting organisation request",
              text: await parseFetchError(error),
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
          },
        );
      }
    },
    orgConsultRequest: function () {
      let vm = this;
      vm.registeringOrg = true;
      let data = new FormData();
      let new_organisation = vm.newOrg;
      for (var organisation in vm.current_user.disturbance_organisations) {
        if (
          new_organisation.abn &&
          vm.current_user.disturbance_organisations[organisation].abn ==
            new_organisation.abn
        ) {
          swal.fire({
            title: "Checking Organisation",
            text: "You are already associated with this organisation.",
            icon: "info",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
          vm.registeringOrg = false;
          vm.uploadedFile = null;
          vm.addingCompany = false;
          vm.resetNewOrg();
          return;
        }
      }
      data.append("name", vm.newOrg.name);
      data.append("abn", vm.newOrg.abn);
      data.append("identification", vm.uploadedFile);
      data.append("role", vm.role);
      vm.newOrg.name = vm.newOrg.name == null ? "" : vm.newOrg.name;
      vm.newOrg.abn = vm.newOrg.abn == null ? "" : vm.newOrg.abn;
      if (
        vm.newOrg.name == "" ||
        vm.newOrg.abn == "" ||
        vm.uploadedFile == null
      ) {
        vm.registeringOrg = false;
        swal.fire({
          title: "Error submitting organisation request",
          text: "Please enter the organisation details and attach a file before submitting your request.",
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
        });
      } else {
        console.log(data);
        let request = fetch_util.fetchUrl(
          api_endpoints.organisation_requests,
          { method: "POST", body: data },
          {},
        );
        request.then(
          () => {
            vm.registeringOrg = false;
            vm.uploadedFile = null;
            vm.addingCompany = false;
            vm.resetNewOrg();
            swal
              .fire({
                title: "Sent",
                text: "Your organisation request has been successfully submitted.",
                icon: "success",
                customClass: {
                  confirmButton: "btn btn-primary",
                },
              })
              .then(() => {
                if (this.$route.name == "account") {
                  window.location.reload(true);
                }
              });
          },
          async (error) => {
            vm.registeringOrg = false;
            swal.fire({
              title: "Error submitting organisation request",
              text: await parseFetchError(error),
              icon: "error",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            });
          },
        );
      }
    },
    uploadNewFileUpdateOrgRequest: function (orgReq) {
      let vm = this;
      vm.readFile();
      let data = new FormData();
      data.append("identification", vm.uploadedFile);
      let request = fetch_util.fetchUrl(
        helpers.add_endpoint_json(
          api_endpoints.organisation_requests,
          orgReq.id + "/reupload_identification_amendment_request",
        ),
        { method: "PUT", body: JSON.stringify(data) },
        {
          emulateJSON: true,
        },
      );
      request.then(
        () => {
          vm.uploadedFile = null;
          vm.resetNewOrg();
          swal
            .fire({
              title: "Sent",
              text: "Your organisation request has been successfully submitted.",
              icon: "success",
              customClass: {
                confirmButton: "btn btn-primary",
              },
            })
            .then(() => {
              window.location.reload(true);
            });
        },
        async (error) => {
          console.log(error);
          vm.registeringOrg = false;
          swal.fire({
            title: "Error submitting organisation request",
            text: await parseFetchError(error),
            icon: "error",
            customClass: {
              confirmButton: "btn btn-primary",
            },
          });
        },
      );
    },
    toggleSection: function (e) {
      let el = e.target;
      let chev = null;
      $(el).on("click", function () {
        chev = $(this);
        $(chev).toggleClass("fa-chevron-down fa-chevron-up");
      });
    },
    fetchOrgRequestPending: function () {
      let vm = this;
      fetch_util
        .fetchUrl(
          helpers.add_endpoint_json(
            api_endpoints.organisation_requests,
            "get_pending_requests",
          ),
        )
        .then((response) => {
          vm.orgRequest_pending = response;
          vm.loading.splice("fetching pending organisation requests", 1);
        })
        .catch((error) => {
          console.log(error);
        });
    },
    fetchOrgRequestAmendmentRequested: function () {
      let vm = this;
      fetch_util
        .fetchUrl(
          helpers.add_endpoint_json(
            api_endpoints.organisation_requests,
            "get_amendment_requested_requests",
          ),
        )
        .then((response) => {
          vm.orgRequest_amendment_requested = response;
          vm.loading.splice(
            "fetching amendment requested organisation requests",
            1,
          );
        })
        .catch((error) => {
          console.log(error);
        });
    },
    unlinkUser: function (org) {
      let vm = this;
      let org_name = org.name;

      swal
        .fire({
          title: "Unlink From Organisation",
          text: "Are you sure you want to be unlinked from " + org.name + " ?",
          icon: "warning",
          showCancelButton: true,
          confirmButtonText: "Unlink",
          cancelButtonText: "Cancel",
          customClass: {
            confirmButton: "btn btn-danger",
            cancelButton: "btn btn-secondary",
          },
        })
        .then(
          (result) => {
            if (result.isConfirmed) {
              let request = fetch_util.fetchUrl(
                helpers.add_endpoint_json(
                  api_endpoints.organisations,
                  org.id + "/unlink_user",
                ),
                { method: "POST", body: JSON.stringify(vm.current_user) },
                {
                  emulateJSON: true,
                },
              );
              request.then(
                () => {
                  let request = fetch_util.fetchUrl(
                    api_endpoints.my_user_details,
                  );
                  request
                    .then((response) => {
                      vm.current_user = response;
                      if (
                        vm.current_user.disturbance_organisations &&
                        vm.current_user.disturbance_organisations.length > 0
                      ) {
                        vm.managesOrg = "Yes";
                      }
                    })
                    .catch((error) => {
                      console.log(error);
                    });
                  swal.fire({
                    title: "Unlink",
                    text:
                      "You have been successfully unlinked from " +
                      org_name +
                      ".",
                    icon: "success",
                    customClass: {
                      confirmButton: "btn btn-primary",
                    },
                  });
                },
                (error) => {
                  swal.fire({
                    title: "Unlink",
                    html:
                      "<p>There was an error unlinking you from " +
                      org_name +
                      ".</p><p>" +
                      error +
                      "</p>",
                    icon: "error",
                    customClass: {
                      confirmButton: "btn btn-primary",
                    },
                  });
                },
              );
            }
          },
          (error) => {
            console.log(error);
          },
        );
    },
  },
  beforeRouteEnter: function (to, from, next) {
    let request = fetch_util.fetchUrl(api_endpoints.my_user_details);
    request
      .then((response) => {
        if (
          to.name == "first-time" &&
          response.address_details &&
          response.personal_details &&
          response.contact_details &&
          response.has_complete_first_time
        ) {
          window.location.href = "/";
        } else {
          next((vm) => {
            vm.current_user = response;
            if (
              vm.current_user.disturbance_organisations &&
              vm.current_user.disturbance_organisations.length > 0
            ) {
              vm.managesOrg = "Yes";
            }
          });
        }
      })
      .catch((error) => {
        console.log(error);
      });
  },
  mounted: function () {
    this.fetchOrgRequestPending();
    this.fetchOrgRequestAmendmentRequested();
    this.personal_form = document.forms.personal_form;
    $('.panelClicker[data-bs-toggle="collapse"]').on("click", function () {
      var chev = $(this).children()[0];
      window.setTimeout(function () {
        $(chev).toggleClass("fa-chevron-down fa-chevron-up");
      }, 100);
    });
    let request = fetch(api_endpoints.is_new_user);
    request
      .then((response) => response.text())
      .then((data) => {
        this.new_user = data;
      })
      .catch((error) => {
        console.log(error);
      });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
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
</style>
