<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-12">
        <FormSection
          :formCollapse="false"
          label="Sites"
          Index="available_sites"
        >
          <div class="map-wrapper">
            <div v-show="!fullscreen" id="filter_search_row_wrapper">
              <div
                class="filter_search_wrapper"
                style="margin-bottom: 5px"
                id="filter_search_row"
              >
                <div
                  v-show="select2Applied"
                  class="bg-light border rounded p-3 shadow-sm mb-3"
                  id="filters_container"
                >
                  <div class="row" id="filters_parent">
                    <label class="col-sm-auto col-form-label">Status</label>
                    <div class="col-sm-3">
                      <select class="form-select" ref="filterStatus"></select>
                    </div>
                    <label class="col-sm-auto col-form-label"
                      >Availability</label
                    >
                    <div class="col-sm-3">
                      <select class="form-select" ref="filterAvailability">
                        <option value="">All</option>
                        <option value="available">Available</option>
                        <option value="unavailable">Unavailable</option>
                      </select>
                    </div>
                    <label class="col-sm-auto col-form-label">Search</label>
                    <div class="col-sm-3">
                      <input
                        v-model="search_text"
                        pattern="[0-9]*"
                        id="search_text"
                        required
                        class="form-control"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div :id="elem_id" class="map" style="position: relative">
              <div :id="search_box_id" class="search-box">
                <input
                  :id="search_input_id"
                  class="search-input"
                  placeholder="longitude, latitude OR address to search"
                />
              </div>
              <div v-show="fullscreen" id="filter_search_on_map">
                <!-- filters on map here -->
              </div>
              <div v-if="loading_sites" class="spinner_on_map">
                <div
                  class="spinner-border text-primary"
                  role="status"
                  style="width: 3rem; height: 3rem"
                >
                  <span class="visually-hidden">Loading...</span>
                </div>
              </div>
              <div class="basemap-button">
                <img
                  id="basemap_sat"
                  :src="satelliteIconUrl"
                  @click="setBaseLayer('sat')"
                />
                <img
                  id="basemap_osm"
                  :src="mapIconUrl"
                  @click="setBaseLayer('osm')"
                />
              </div>
              <div class="optional-layers-wrapper">
                <div class="optional-layers-button">
                  <template v-if="mode === 'layer'">
                    <img :src="infoBubbleSvgUrl" @click="set_mode('measure')" />
                  </template>
                  <template v-else>
                    <img :src="rulerSvgUrl" @click="set_mode('layer')" />
                  </template>
                </div>
                <div style="position: relative">
                  <transition v-if="optionalLayers.length">
                    <div
                      class="optional-layers-button"
                      @mouseover="hover = true"
                      v-if="optionalLayers.length"
                    >
                      <img :src="layersSvgUrl" />
                    </div>
                  </transition>
                  <transition v-if="optionalLayers.length">
                    <div
                      div
                      class="layer_options overflow-y-auto"
                      v-show="hover"
                      @mouseleave="hover = false"
                      style="height: 350px"
                    >
                      <div
                        v-for="layer in optionalLayers"
                        :key="layer.ol_uid"
                        class="form-check"
                      >
                        <input
                          type="checkbox"
                          :id="layer.ol_uid"
                          :checked="layer.values_.visible"
                          @change="changeLayerVisibility(layer)"
                          class="form-check-input layer_option"
                        />
                        <label
                          :for="layer.ol_uid"
                          class="form-check-label fw-normal"
                          >{{ layer.get("title") }}</label
                        >
                      </div>
                    </div>
                  </transition>
                </div>
              </div>
            </div>
            <div class="button_row">
              <span class="view_all_button" @click="displayAllFeatures"
                >View All On Map</span
              >
            </div>
          </div>
          <div :id="popup_id" class="ol-popup">
            <a href="#" :id="popup_closer_id" class="ol-popup-closer">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                version="1.1"
                height="20"
                width="20"
                class="close-icon"
              >
                <g transform="scale(3)">
                  <path
                    d="M 5.2916667,2.6458333 A 2.6458333,2.6458333 0 0 1 2.6458335,5.2916667 2.6458333,2.6458333 0 0 1 0,2.6458333 2.6458333,2.6458333 0 0 1 2.6458335,0 2.6458333,2.6458333 0 0 1 5.2916667,2.6458333 Z"
                    style="
                      fill: #ffffff;
                      fill-opacity: 1;
                      stroke-width: 0.182031;
                    "
                    id="path846"
                  />
                  <path
                    d="M 1.5581546,0.94474048 2.6457566,2.0324189 3.7334348,0.94474048 4.3469265,1.5581547 3.2592475,2.6458334 4.3469265,3.7334353 3.7334348,4.3469261 2.6457566,3.2593243 1.5581546,4.3469261 0.9447402,3.7334353 2.0323422,2.6458334 0.9447402,1.5581547 Z"
                    style="
                      fill: #f46464;
                      fill-opacity: 1;
                      stroke: none;
                      stroke-width: 0.0512157;
                    "
                    id="path2740-3"
                  />
                </g>
              </svg>
            </a>
            <div :id="popup_content_id"></div>
          </div>
        </FormSection>

        <ContactLicenceHolderModal
          ref="contact_licence_holder_modal"
          :key="modalBindId"
          @contact_licence_holder="contactLicenceHolderOK"
        />
      </div>
    </div>
  </div>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue";
import ContactLicenceHolderModal from "@/components/common/apiary/contact_licence_holder_modal.vue";
import { v4 as uuid } from "uuid";
import { markRaw } from "vue";

import "ol/ol.css";
import "ol-layerswitcher/dist/ol-layerswitcher.css";
import "@/components/common/apiary/index.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import TileWMS from "ol/source/TileWMS";
import { fromLonLat, toLonLat } from "ol/proj";
import { Draw, Modify } from "ol/interaction";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from "ol/style";
import {
  FullScreen as FullScreenControl,
  MousePosition as MousePositionControl,
} from "ol/control";
import { LineString, Point } from "ol/geom";
import GeoJSON from "ol/format/GeoJSON";
import Overlay from "ol/Overlay";
import {
  getDisplayNameFromStatus,
  getDisplayNameOfCategory,
  getStatusForColour,
  getApiaryFeatureStyle,
  zoomToCoordinates,
  checkIfValidlatitudeAndlongitude,
} from "@/components/common/apiary/site_colours.js";
import MeasureStyles, {
  formatLength,
} from "@/components/common/apiary/measure.js";
import Cluster from "ol/source/Cluster";
import "select2/dist/css/select2.min.css";
import Awesomplete from "awesomplete";
import { api_endpoints } from "@/utils/hooks";
import { parseFetchError } from "@/utils/helpers";
import $ from "jquery";

export default {
  name: "AvailableSites",
  data: function () {
    let default_show_statuses = [
      "vacant",
      "pending",
      "denied",
      "current",
      "not_to_be_reissued",
      "suspended",
    ];
    let default_show_availabilities = ["available", "unavailable"];

    return {
      debug: true,
      modalBindId: uuid(),

      show_action_make_vacant: true,
      show_action_contact_licence_holder: true,

      map: null,
      apiarySitesQuerySource: null,
      apiarySitesClusterLayer: null,
      elem_id: uuid(),
      popup_id: uuid(),
      popup_closer_id: uuid(),
      popup_content_id: uuid(),
      overlay: null,
      content_element: null,
      modifyInProgressList: [],
      tileLayerOsm: null,
      tileLayerSat: null,
      optionalLayers: [],
      hover: false,
      mode: "normal",
      drawForMeasure: null,
      measurementLayer: null,
      style: MeasureStyles.defaultStyle,
      segmentStyle: MeasureStyles.segmentStyle,
      labelStyle: MeasureStyles.labelStyle,
      segmentStyles: null,

      filter_selected_names: "select status",
      search_text: "",
      fullscreen: false,
      num_of_status_selection: 0, // Store the number of selection at the UI (not cache)
      num_of_availability_selection: 0, // Store the number of selection at the UI (not cache)

      useSelect2: true,
      select2Applied: false,
      filterStatuses: [],
      select2Obj: null,

      all_sites_ajax_obj: null,
      all_sites_loading: false,

      show_hide_instructions: [
        // This array is used as instructions when showing/hiding the apiary sites on the map
        // ApiarySite
        {
          id: "vacant",
          text: "Vacant",
          show: default_show_statuses.includes("vacant"),
          api: "list_apiary_sites_vacant",
          features_and_rows: [],
          ajax_obj: null,
          loading_sites: false,
        },
        // ApiarySiteOnProposal
        {
          id: "pending",
          text: "Pending",
          show: default_show_statuses.includes("pending"),
          api: "list_apiary_sites_pending",
          features_and_rows: [],
          ajax_obj: null,
          loading_sites: false,
        },
        {
          id: "denied",
          text: "Denied",
          show: default_show_statuses.includes("denied"),
          api: "list_apiary_sites_denied",
          features_and_rows: [],
          ajax_obj: null,
          loading_sites: false,
        },
        // ApiarySiteOnApproval
        {
          id: "current",
          text: "Current",
          show: default_show_statuses.includes("current"),
          api: "list_apiary_sites_current",
          features_and_rows: [],
          ajax_obj: null,
          options: [
            {
              id: "available",
              text: "Available",
              show: default_show_availabilities.includes("available"),
              api: "list_apiary_sites_current_available",
              features_and_rows: [],
              ajax_obj: null,
              loading_sites: false,
            },
            {
              id: "unavailable",
              text: "Unavailable",
              show: default_show_availabilities.includes("unavailable"),
              api: "list_apiary_sites_current_unavailable",
              features_and_rows: [],
              ajax_obj: null,
              loading_sites: false,
            },
          ],
        },
        {
          id: "not_to_be_reissued",
          text: "Not to be reissued",
          show: default_show_statuses.includes("not_to_be_reissued"),
          api: "list_apiary_sites_not_to_be_reissued",
          features_and_rows: [],
          ajax_obj: null,
          loading_sites: false,
        },
        {
          id: "suspended",
          text: "Suspended",
          show: default_show_statuses.includes("suspended"),
          api: "list_apiary_sites_suspended",
          features_and_rows: [],
          ajax_obj: null,
          loading_sites: false,
        },
      ],
      filter_status_options: [
        {
          id: "vacant",
          text: "Vacant",
        },
        {
          id: "pending",
          text: "Pending",
        },
        {
          id: "denied",
          text: "Denied",
        },
        {
          id: "current",
          text: "Current",
        },
        {
          id: "not_to_be_reissued",
          text: "Not to be reissued",
        },
        {
          id: "suspended",
          text: "Suspended",
        },
      ],
      filter_availability_options: [
        {
          id: "all",
          text: "All",
        },
        {
          id: "available",
          text: "Available",
        },
        {
          id: "unavailable",
          text: "Unavailable",
        },
      ],
      awe: null,
      search_box_id: uuid(),
      search_input_id: uuid(),
      search_address_latlng_text: "",

      // AT the moment (specify the path) this works but not ideal, need to find a way to load images from assets folder
      satelliteIconUrl: "/static/disturbance_vue/src/satellite_icon.jpg",
      mapIconUrl: "/static/disturbance_vue/src/map_icon.png",
      layersSvgUrl: "/static/disturbance_vue/src/layers.svg",
      rulerSvgUrl: "/static/disturbance_vue/src/ruler.svg",
      infoBubbleSvgUrl: "/static/disturbance_vue/src/info-bubble.svg",
    };
  },
  components: {
    FormSection,
    ContactLicenceHolderModal,
  },
  props: {
    is_external: {
      type: Boolean,
      default: false,
    },
    is_internal: {
      type: Boolean,
      default: false,
    },
    can_modify: {
      type: Boolean,
      default: false,
    },
    display_at_time_of_submitted: {
      type: Boolean,
      default: false,
    },
  },
  watch: {
    search_text: function () {
      // Clear data storage in the filters
      let vm = this;

      for (let site_status of vm.show_hide_instructions) {
        if (site_status.options) {
          for (let option of site_status.options) {
            if (option.show) {
              for (let feature_and_row of option.features_and_rows) {
                try {
                  // Remove the apiary_site from the map
                  vm.apiarySitesQuerySource.removeFeature(
                    feature_and_row.feature,
                  );
                } catch (err) {
                  console.log(err);
                }
              }
            }
          }
        } else {
          if (site_status.show) {
            //let rows_jquery = []
            for (let feature_and_row of site_status.features_and_rows) {
              try {
                // Remove the apiary_site from the map
                vm.apiarySitesQuerySource.removeFeature(
                  feature_and_row.feature,
                );
              } catch (err) {
                console.log(err);
              }
            }
          }
        }
        site_status.features_and_rows = [];
        if (site_status.options) {
          for (let option of site_status.options) {
            option.features_and_rows = [];
          }
        }
      }
      vm.showHideApiarySites();
    },
  },
  computed: {
    ruler_colour: function () {
      if (this.mode === "normal") {
        return "#aaa";
      } else {
        return "#53c2cf";
      }
    },
    loading_sites: function () {
      return this.all_sites_loading;
    },
  },
  methods: {
    initAwesomplete: function () {
      var vm = this;
      var element_search = document.getElementById(vm.search_input_id);
      this.awe = new Awesomplete(element_search);
      $(element_search)
        .on("keyup", function (ev) {
          var keyCode = ev.keyCode || ev.which;
          if (
            (48 <= keyCode && keyCode <= 90) ||
            (96 <= keyCode && keyCode <= 105) ||
            keyCode === 8 ||
            keyCode === 46
          ) {
            vm.search(ev.target.value);
            return false;
          }
        })
        .on("awesomplete-selectcomplete", function (ev) {
          ev.preventDefault();
          ev.stopPropagation();

          let currentZoomLevel = vm.map.getView().getZoom();
          let targetZoomLevel = 14;
          if (targetZoomLevel < currentZoomLevel) {
            targetZoomLevel = currentZoomLevel;
          }

          /* User selected one of the search results */
          for (var i = 0; i < vm.suggest_list.length; i++) {
            if (vm.suggest_list[i].value == ev.target.value) {
              var latlng = {
                lat: vm.suggest_list[i].feature.geometry.coordinates[1],
                lng: vm.suggest_list[i].feature.geometry.coordinates[0],
              };
              zoomToCoordinates(
                vm.map,
                fromLonLat([latlng.lng, latlng.lat]),
                targetZoomLevel,
              );
            }
          }
          return false;
        });
    },
    search: function (place) {
      var vm = this;

      let searching_by_latlng = checkIfValidlatitudeAndlongitude(place);

      if (!searching_by_latlng) {
        var latlng = toLonLat(vm.map.getView().getCenter());
        $.ajax({
          url:
            api_endpoints.geocoding_address_search +
            encodeURIComponent(place) +
            ".json?" +
            $.param({
              country: "au",
              limit: 10,
              proximity: "" + latlng[0] + "," + latlng[1],
              bbox: "112.920934,-35.191991,129.0019283,-11.9662455",
              types:
                "region,postcode,district,place,locality,neighborhood,address,poi",
            }),
          dataType: "json",
          success: function (data) {
            vm.suggest_list = []; // Clear the list first
            if (data.features && data.features.length > 0) {
              for (var i = 0; i < data.features.length; i++) {
                vm.suggest_list.push({
                  label: data.features[i].place_name,
                  value: data.features[i].place_name,
                  feature: data.features[i],
                });
              }
            }

            vm.awe.list = vm.suggest_list;
            vm.awe.evaluate();
          },
        });
      } else {
        let lat = searching_by_latlng[1];
        let lng = searching_by_latlng[4];
        let currentZoomLevel = vm.map.getView().getZoom();
        let targetZoomLevel = 14;
        if (targetZoomLevel < currentZoomLevel) {
          targetZoomLevel = currentZoomLevel;
        }
        //zoomToCoordinates(vm.map, [lng, lat], targetZoomLevel)
        zoomToCoordinates(vm.map, fromLonLat([lat, lng]), targetZoomLevel);
      }
    },
    updateAvailabilityInstructions: function (
      availabilities_currently_selected,
      options,
    ) {
      if (availabilities_currently_selected.length === 0) {
        for (let option of options) {
          option.show = true;
        }
      } else {
        for (let option of options) {
          if (availabilities_currently_selected.includes(option.id)) {
            option.show = true;
          } else {
            option.show = false;
          }
        }
      }
    },
    updateInstructions: function () {
      let vm = this;
      let statuses_currently_selected = $(vm.$refs.filterStatus)
        .select2("data")
        .map((x) => {
          return x.id;
        });
      // filterAvailability is a plain <select> — read its value directly
      let avail_val = $(vm.$refs.filterAvailability).val();
      let availabilities_currently_selected = avail_val ? [avail_val] : [];
      let current_status_item = vm.show_hide_instructions.filter((x) => {
        return x.id === "current";
      })[0]; // We just interested in the 'current' status

      if (availabilities_currently_selected.length === 0) {
        // No availabilities selected
        if (statuses_currently_selected.length === 0) {
          // No statuses selected --> Show all
          for (let site_status of vm.show_hide_instructions) {
            site_status.show = true;
          }
        } else {
          // some statuses selected --> Show whatever selected
          for (let site_status of vm.show_hide_instructions) {
            if (statuses_currently_selected.includes(site_status.id)) {
              site_status.show = true;
            } else {
              site_status.show = false;
            }
          }
        }
      } else {
        // Some availability selected
        if (statuses_currently_selected.length === 0) {
          // No statuses selected --> Show only current
          for (let site_status of vm.show_hide_instructions) {
            if (site_status.id === "current") {
              site_status.show = true;
              continue;
            }
            site_status.show = false;
          }
        } else {
          // Some statuses selected
          for (let site_status of vm.show_hide_instructions) {
            if (site_status.id === "current") {
              if (statuses_currently_selected.includes(site_status.id)) {
                site_status.show = true;
                continue;
              }
            }
            site_status.show = false;
          }
        }
      }
      vm.updateAvailabilityInstructions(
        availabilities_currently_selected,
        current_status_item.options,
      );
    },
    toggleFilterSearchRow: function (action) {
      // Attach/Detach filter-search elements to/from the map
      let vm = this;
      let filter_search_elements = $("#filter_search_row");
      let filter_search_row_wrapper = $("#filter_search_row_wrapper");
      let wrapper_in_map = $("#filter_search_on_map");

      let search_box = $("#" + vm.search_box_id);

      if (action === "enter") {
        filter_search_elements.prependTo(wrapper_in_map);
        search_box.css("top", "50px");
        search_box.css("left", "60px");
      } else if (action === "leave") {
        filter_search_elements.prependTo(filter_search_row_wrapper);
        search_box.css("top", "10px");
        search_box.css("left", "50px");
      }
    },
    applySelect2: function () {
      let vm = this;

      if (!vm.select2Applied) {
        $(vm.$refs.filterStatus)
          .select2({
            theme: "bootstrap-5",
            allowClear: false,
            placeholder: "Select Status",
            multiple: true,
            data: vm.filter_status_options,
            dropdownParent: $("#filters_parent"),
          })
          .on("select2:select", function () {
            vm.updateInstructions();
            vm.showHideApiarySites();
          })
          .on("select2:unselect", function () {
            vm.updateInstructions();
            vm.showHideApiarySites();
          });

        // filterAvailability is a plain <select>; wire up its change event
        $(vm.$refs.filterAvailability).on("change", function () {
          vm.updateInstructions();
          vm.showHideApiarySites();
        });
        vm.select2Applied = true;
      }
    },
    clearApiarySitesFromMap: function () {
      this.apiarySitesQuerySource.clear();
    },
    clearAjaxObjects: function () {
      let vm = this;
      if (vm.all_sites_ajax_obj != null) {
        vm.all_sites_ajax_obj.abort();
        vm.all_sites_ajax_obj = null;
      }
    },
    addApiarySitesToMap: function (apiary_sites_geojson) {
      let features = new GeoJSON().readFeatures(apiary_sites_geojson, {
        featureProjection: "EPSG:3857",
      });
      this.apiarySitesQuerySource.addFeatures(features);
    },
    addEventListeners: function () {
      let vm = this;

      $("#app").on(
        "click",
        "a[data-contact-licence-holder]",
        this.contactLicenceHolder,
      );
      $("#app").on("click", "a[data-make-vacant]", this.makeVacantClicked);

      let search_input_elem = $("#" + vm.search_input_id);
      search_input_elem.on("input", function (ev) {
        vm.search(ev.target.value);
      });
    },
    getApiarySiteAvailableFromEvent(e) {
      let apiary_site_available = e.target.getAttribute(
        "data-apiary-site-available",
      );

      if (!apiary_site_available) {
        apiary_site_available = e.target
          .getElementsByTagName("span")[0]
          .getAttribute("data-apiary-site-available");
      }

      return apiary_site_available;
    },
    toggleAvailability: async function (e) {
      let apiary_site_id = e.target.getAttribute("data-toggle-availability");
      let current_availability = this.getApiarySiteAvailableFromEvent(e);
      let requested_availability =
        current_availability === "true" ? false : true;
      e.stopPropagation();

      try {
        const response = await fetch(
          "/api/apiary_site/" + apiary_site_id + "/toggle_availability/",
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              // Add authorization headers if needed
            },
            body: JSON.stringify({ available: requested_availability }),
          },
        );
        console.log(response);
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText);
        }

        const site_updated = await response.json();
        // Update the site in the table
        console.log("Site updated:", site_updated);
      } catch (error) {
        swal.fire({
          title: "Submit Error",
          text: error,
          icon: "error",
          customClass: {
            confirmButton: "btn btn-primary",
          },
        });
      }
    },
    makeVacantClicked: function (e) {
      console.log("makeVacantClicked");
      let vm = this;
      let apiary_site_id = e.target.getAttribute("data-make-vacant");
      e.stopPropagation();

      swal
        .fire({
          title: "Make Vacant",
          text:
            "Are you sure you want to make this apiary site: " +
            apiary_site_id +
            " vacant?",
          icon: "question",
          showCancelButton: true,
          confirmButtonText: "Yes, make vacant",
          customClass: {
            confirmButton: "btn btn-primary",
            cancelButton: "btn btn-secondary",
          },
        })
        .then((result) => {
          if (result.isConfirmed) {
            fetch("/api/apiary_site/" + apiary_site_id + "/make_vacant/", {
              method: "PATCH",
              headers: {
                "Content-Type": "application/json",
                // Add authorization headers if needed
              },
              body: JSON.stringify({ status: "vacant" }),
            })
              .then(async (response) => {
                if (!response.ok) {
                  const errorText = await response.text();
                  throw new Error(errorText);
                }
                // Remove the row from the table
                $(e.target)
                  .closest("tr")
                  .fadeOut("slow", function () {
                    // Remove the site table which the table is based on
                    vm.removeApiarySiteById(apiary_site_id);
                  });
              })
              .catch(async (error) => {
                console.log(error);
                const errorMessage = await parseFetchError(error);
                swal.fire({
                  title: "Error Making Site Vacant",
                  text: errorMessage,
                  icon: "error",
                  customClass: {
                    confirmButton: "btn btn-primary",
                  },
                });
              });
          }
        });
    },
    toggleStatusFilterDropdown: function () {
      $(".status_filter_dropdown").slideToggle("fast");
    },
    mouseEnter: function (e) {
      let vm = this;
      if (!vm.not_close_popup_by_mouseleave) {
        let apiary_site_id = e.currentTarget.getAttribute(
          "data-apiary-site-id",
        );
        if (apiary_site_id) {
          vm.showPopupById(apiary_site_id);
        }
      }
    },
    mouseLeave: function () {
      let vm = this;
      if (!vm.not_close_popup_by_mouseleave) {
        //vm.$refs.component_map.closePopup()
        vm.closePopup();
      }
    },
    zoomOnApiarySite: function (e) {
      this.not_close_popup_by_mouseleave = true;

      let apiary_site_id = e.target.getAttribute("data-view-on-map");
      this.zoomToApiarySiteById(apiary_site_id);
      e.stopPropagation();
    },
    setBaseLayer: function (selected_layer_name) {
      let vm = this;
      if (selected_layer_name == "sat") {
        vm.tileLayerOsm.setVisible(false);
        vm.tileLayerSat.setVisible(true);
        $("#basemap_sat").hide();
        $("#basemap_osm").show();
      } else {
        vm.tileLayerOsm.setVisible(true);
        vm.tileLayerSat.setVisible(false);
        $("#basemap_osm").hide();
        $("#basemap_sat").show();
      }
    },
    set_mode: function (mode) {
      this.mode = mode;
      if (this.mode === "layer") {
        this.clearMeasurementLayer();
        this.drawForMeasure.setActive(false);
      } else if (this.mode === "measure") {
        this.drawForMeasure.setActive(true);
      }
    },
    addJoint: function (point, styles) {
      let s = new Style({
        image: new CircleStyle({
          radius: 2,
          fill: new Fill({
            color: "#3399cc",
          }),
        }),
      });
      s.setGeometry(point);
      styles.push(s);

      return styles;
    },
    styleFunctionForMeasurement: function (feature, resolution) {
      console.log(resolution);
      let vm = this;
      let for_layer = feature.get("for_layer", false);

      const styles = [];
      styles.push(vm.style); // This style is for the feature itself
      styles.push(vm.segmentStyle);

      ///////
      // From here, adding labels and tiny circles at the end points of the linestring
      ///////
      const geometry = feature.getGeometry();
      if (geometry.getType() === "LineString") {
        let segment_count = 0;
        geometry.forEachSegment(function (a, b) {
          const segment = new LineString([a, b]);
          const label = formatLength(segment);
          const segmentPoint = new Point(segment.getCoordinateAt(0.5));

          // Add a style for this segment
          let segment_style = vm.segmentStyle.clone(); // Because there could be multilpe segments, we should copy the style per segment
          segment_style.setGeometry(segmentPoint);
          segment_style.getText().setText(label);
          styles.push(segment_style);

          if (segment_count == 0) {
            // Add a tiny circle to the very first coordinate of the linestring
            let p = new Point(a);
            vm.addJoint(p, styles);
          }
          // Add tiny circles to the end of the linestring
          let p = new Point(b);
          vm.addJoint(p, styles);

          segment_count++;
        });
      }

      if (!for_layer) {
        // We don't need the last label when draw on the layer.
        let label_on_mouse = formatLength(geometry); // Total length of the linestring
        let point = new Point(geometry.getLastCoordinate());
        vm.labelStyle.setGeometry(point);
        vm.labelStyle.getText().setText(label_on_mouse);
        styles.push(vm.labelStyle);
      }

      return styles;
    },
    clearMeasurementLayer: function () {
      let vm = this;
      let features = vm.measurementLayer.getSource().getFeatures();
      features.forEach((feature) => {
        vm.measurementLayer.getSource().removeFeature(feature);
      });
    },
    changeLayerVisibility: function (targetLayer) {
      targetLayer.setVisible(!targetLayer.getVisible());
    },
    addOptionalLayers: function () {
      let vm = this;
      fetch("/api/map_layers/")
        .then(async (response) => {
          if (!response.ok) {
            return response.json().then((err) => {
              throw err;
            });
          }
          let layers = await response.json();
          for (var i = 0; i < layers.length; i++) {
            let l = new TileWMS({
              url: layers[i].layer_group_name
                ? `/kb-proxy/geoserver/${layers[i].layer_group_name}/wms`
                : "/kb-proxy/geoserver/wms",
              params: {
                FORMAT: "image/png",
                VERSION: "1.1.1",
                tiled: true,
                STYLES: "",
                LAYERS: layers[i].layer_full_name,
              },
            });

            let tileLayer = markRaw(
              new TileLayer({
                title: layers[i].display_name.trim(),
                visible: false,
                source: l,
              }),
            );

            // Set additional attributes to the layer
            tileLayer.set("columns", layers[i].columns);
            tileLayer.set("display_all_columns", layers[i].display_all_columns);

            vm.optionalLayers.push(tileLayer);
            vm.map.addLayer(tileLayer);
          }
        })
        .catch((error) => {
          console.log(error);
        });
    },
    closePopup: function () {
      this.content_element.innerHTML = null;
      this.overlay.setPosition(undefined);
      this.not_close_popup_by_mouseleave = false;
      //this.$emit('popupClosed')
    },
    forceToRefreshMap: function () {
      let vm = this;
      setTimeout(function () {
        vm.map.updateSize();
      }, 50);
    },
    initMap: function () {
      let vm = this;

      const streetLayer = env["kb_basemap_street_layer"] || "";
      const satelliteLayer = env["kb_basemap_satellite_layer"] || "";
      const streetNamespace =
        streetLayer.indexOf(":") > -1 ? streetLayer.split(":")[0] : "";
      const satelliteNamespace =
        satelliteLayer.indexOf(":") > -1 ? satelliteLayer.split(":")[0] : "";

      let streetTileWms = new TileWMS({
        url: streetNamespace
          ? `/kb-proxy/geoserver/${streetNamespace}/wms`
          : "/kb-proxy/geoserver/wms",
        params: {
          FORMAT: "image/png",
          VERSION: "1.1.1",
          tiled: true,
          STYLES: "",
          LAYERS: streetLayer,
        },
      });

      let satelliteTileWms = new TileWMS({
        url: satelliteNamespace
          ? `/kb-proxy/geoserver/${satelliteNamespace}/wms`
          : "/kb-proxy/geoserver/wms",
        params: {
          FORMAT: "image/png",
          VERSION: "1.1.1",
          tiled: true,
          STYLES: "",
          LAYERS: satelliteLayer,
        },
      });

      vm.tileLayerOsm = markRaw(
        new TileLayer({
          title: "Street",
          type: "base",
          visible: true,
          source: streetTileWms,
        }),
      );

      vm.tileLayerSat = markRaw(
        new TileLayer({
          title: "Satellite",
          type: "base",
          visible: true,
          source: satelliteTileWms,
        }),
      );

      vm.map = markRaw(
        new Map({
          layers: [vm.tileLayerOsm, vm.tileLayerSat],
          //target: 'map',
          target: vm.elem_id,
          view: new View({
            center: fromLonLat([115.95, -31.95]),
            zoom: 7,
          }),
          pixelRatio: 1, // We need this in order to make this map work correctly with the browser and/or display scaling factor(s) other than 100%
          // Ref: https://github.com/openlayers/openlayers/issues/11464
        }),
      );

      vm.apiarySitesQuerySource = markRaw(new VectorSource({}));

      let clusterSource = markRaw(
        new Cluster({
          distance: 50,
          source: vm.apiarySitesQuerySource,
        }),
      );

      let styleCache = {};
      vm.apiarySitesClusterLayer = markRaw(
        new VectorLayer({
          title: "Cluster Layer",
          source: clusterSource,
          style: function (clusteredFeature) {
            let featuresInClusteredFeature = clusteredFeature.get("features");
            let size = featuresInClusteredFeature.length;
            let style = styleCache[size];
            if (size == 1) {
              // When size is 1, which means the cluster feature has only one site
              // we want to display it as dedicated style
              let status = getStatusForColour(featuresInClusteredFeature[0]);
              return getApiaryFeatureStyle(status);
            }
            let radius_in_pixel = 16;
            if (size < 10) {
              radius_in_pixel = 10;
            } else if (size < 100) {
              radius_in_pixel = 12;
            } else if (size < 1000) {
              radius_in_pixel = 14;
            }
            if (!style) {
              style = new Style({
                image: new CircleStyle({
                  radius: radius_in_pixel,
                  stroke: new Stroke({
                    color: "#fff",
                  }),
                  fill: new Fill({
                    color: "#3399cc",
                  }),
                }),
                text: new Text({
                  text: size.toString(),
                  fill: new Fill({
                    color: "#fff",
                  }),
                }),
              });
              styleCache[size] = style;
            }
            return style;
          },
        }),
      );
      vm.map.addLayer(vm.apiarySitesClusterLayer);
      vm.apiarySitesClusterLayer.setZIndex(10);

      // Full screen toggle
      let fullScreenControl = new FullScreenControl();
      fullScreenControl.on("enterfullscreen", function () {
        vm.fullscreen = true;
        vm.toggleFilterSearchRow("enter");
      });
      fullScreenControl.on("leavefullscreen", function () {
        vm.fullscreen = false;
        vm.toggleFilterSearchRow("leave");
      });
      vm.map.addControl(fullScreenControl);

      // Measure tool
      let draw_source = new VectorSource({ wrapX: false });
      vm.drawForMeasure = new Draw({
        source: draw_source,
        type: "LineString",
        style: vm.styleFunctionForMeasurement,
      });
      // Set a custom listener to the Measure tool
      vm.drawForMeasure.set("escKey", "");
      vm.drawForMeasure.on("change:escKey", function () {
        //vm.drawForMeasure.finishDrawing()
      });
      vm.drawForMeasure.on("drawstart", function () {
        vm.measuring = true;
      });
      vm.drawForMeasure.on("drawend", function () {
        vm.measuring = false;
      });

      // Create a layer to retain the measurement
      vm.measurementLayer = new VectorLayer({
        title: "Measurement Layer",
        source: draw_source,
        style: function (feature, resolution) {
          feature.set("for_layer", true);
          return vm.styleFunctionForMeasurement(feature, resolution);
        },
      });
      vm.map.addInteraction(vm.drawForMeasure);
      vm.map.addLayer(vm.measurementLayer);

      // Show mouse coordinates
      vm.map.addControl(
        new MousePositionControl({
          coordinateFormat: function (coords) {
            let message = vm.getDegrees(toLonLat(coords)) + "\n";
            return message;
          },
          target: document.getElementById("mouse-position"),
          className: "custom-mouse-position",
        }),
      );

      let container = document.getElementById(vm.popup_id);
      vm.content_element = document.getElementById(vm.popup_content_id);
      let closer = document.getElementById(vm.popup_closer_id);

      vm.overlay = new Overlay({
        element: container,
        autoPan: false,
        offest: [0, -10],
      });

      closer.onclick = function () {
        vm.closePopup();
        closer.blur();
        return false;
      };

      vm.map.addOverlay(vm.overlay);

      vm.map.on("singleclick", function (evt) {
        if (vm.mode === "layer") {
          let feature = vm.map.forEachFeatureAtPixel(
            evt.pixel,
            function (feature) {
              return feature;
            },
          );
          if (feature) {
            let features = feature.get("features");
            if (features.length == 1) {
              if (!feature.id) {
                // When the Modify object is used for the layer, 'feature' losts some of the attributes including 'id', 'status'...
                // Therefore try to get the correct feature by the coordinate
                let geometry = feature.getGeometry();
                let coord = geometry.getCoordinates();
                feature =
                  vm.apiarySitesQuerySource.getFeaturesAtCoordinate(coord);
              }
              vm.showPopup(feature[0]);
            } else {
              let geometry = feature.getGeometry();
              let coordinates = geometry.getCoordinates();
              let currentZoomLevel = vm.map.getView().getZoom();
              zoomToCoordinates(vm.map, coordinates, currentZoomLevel + 1);
            }
          } else {
            vm.closePopup();
            let view = vm.map.getView();
            let viewResolution = view.getResolution();

            // Retrieve active layers' sources
            for (let i = 0; i < vm.optionalLayers.length; i++) {
              let visibility = vm.optionalLayers[i].getVisible();
              if (visibility) {
                // Retrieve column names to be displayed
                let column_names = vm.optionalLayers[i].get("columns");
                column_names = column_names.map(function (col) {
                  // Convert array of dictionaries to simple array
                  if (vm.is_internal && col.option_for_internal) {
                    return col.name;
                  }
                  if (vm.is_external && col.option_for_external) {
                    return col.name;
                  }
                });
                // Retrieve the value of display_all_columns boolean flag
                let display_all_columns = vm.optionalLayers[i].get(
                  "display_all_columns",
                );

                // Retrieve the URL to query the attributes
                let source = vm.optionalLayers[i].getSource();
                let url = source.getFeatureInfoUrl(
                  evt.coordinate,
                  viewResolution,
                  view.getProjection(),
                  //{'INFO_FORMAT': 'text/html'}
                  { INFO_FORMAT: "application/json" },
                );

                // Query
                let p = fetch(url, {
                  credentials: "include",
                });

                //p.then(res => res.text()).then(function(data){
                p.then((res) => res.json()).then(function (data) {
                  vm.showPopupForLayersJson(
                    data,
                    evt.coordinate,
                    column_names,
                    display_all_columns,
                    vm.optionalLayers[i],
                  );
                });
              }
            }
          }
        } else if (vm.mode === "measure") {
          // When in measure mode, the styleFunction() is responsible for the drawing
        }
      });
      vm.map.on("pointermove", function (e) {
        if (e.dragging) return;
        let pixel = vm.map.getEventPixel(e.originalEvent);
        let hit = vm.map.hasFeatureAtPixel(pixel);
        vm.map.getTargetElement().style.cursor = hit ? "pointer" : "";
      });
      vm.map.on("moveend", function () {
        let extent = vm.map.getView().calculateExtent(vm.map.getSize());
        let features = vm.apiarySitesQuerySource.getFeaturesInExtent(extent);
        vm.$emit("featuresDisplayed", features);
      });
      if (vm.can_modify) {
        let modifyTool = new Modify({
          source: vm.apiarySitesQuerySource,
        });
        modifyTool.on("modifystart", function (attributes) {
          attributes.features.forEach(function () {});
        });
        modifyTool.on("modifyend", function (attributes) {
          attributes.features.forEach(function (feature) {
            let id = feature.getId();
            let index = vm.modifyInProgressList.indexOf(id);
            if (index != -1) {
              // feature has been modified
              vm.modifyInProgressList.splice(index, 1);
              let coords = toLonLat(feature.getGeometry().getCoordinates());
              vm.$emit("featureGeometryUpdated", {
                id: id,
                coordinates: { lng: coords[0], lat: coords[1] },
              });
            }
          });
        });
        vm.map.addInteraction(modifyTool);
      }
      document.addEventListener("keydown", vm.keydown, false);
    },
    keydown: function (evt) {
      let vm = this;

      let charCode = evt.which ? evt.which : evt.keyCode;
      if (charCode === 27 && vm.measuring === true) {
        //esc key
        //dispatch event
        this.drawForMeasure.set("escKey", Math.random());
      }
    },
    showPopupById: function (apiary_site_id) {
      let feature = this.apiarySitesQuerySource.getFeatureById(apiary_site_id);
      this.showPopup(feature);
    },
    get_approval_link: function (feature) {
      let approval_link = "";
      if (feature.get("approval_id") && this.is_internal) {
        approval_link =
          "<tr>" +
          '<th scope="row">Licence</th>' +
          '<td><a href="/internal/approval/' +
          feature.get("approval_id") +
          '">' +
          feature.get("lodgement_number") +
          "</a></td>" +
          "</tr>";
      }
      return approval_link;
    },
    get_actions: function (feature) {
      let action_list = [];

      let a_status = getStatusForColour(
        feature,
        false,
        this.display_at_time_of_submitted,
      );

      if (this.is_internal && this.show_action_make_vacant) {
        if (["denied", "not_to_be_reissued"].includes(a_status)) {
          let display_text = "Make Vacant";
          let ret =
            '<a href="#' +
            feature.id_ +
            '" data-make-vacant="' +
            feature.id_ +
            '">' +
            display_text +
            "</a>";
          action_list.push(ret);
        }
      }
      if (this.is_external && this.show_action_contact_licence_holder) {
        if (["current"].includes(a_status)) {
          let available = feature.get("available");
          if (available) {
            let display_text = "Contact licence holder";
            let ret =
              '<a href="#' +
              feature.id_ +
              '" data-contact-licence-holder="' +
              feature.id_ +
              '">' +
              display_text +
              "</a>";
            action_list.push(ret);
          }
        }
      }
      let ret_str = action_list.join("<br />");
      return ret_str;
    },
    showPopup: function (feature) {
      let unique_id = uuid();

      if (feature) {
        let geometry = feature.getGeometry();
        let coord = geometry.getCoordinates();
        let svg_hexa =
          "<svg xmlns='http://www.w3.org/2000/svg' version='1.1' height='20' width='15'>" +
          '<g transform="translate(0, 4) scale(0.9)"><path d="M 14.3395,12.64426 7.5609998,16.557828 0.78249996,12.64426 0.7825,4.8171222 7.5609999,0.90355349 14.3395,4.8171223 Z" id="path837" style="fill:none;stroke:#ffffff;stroke-width:1.565;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1" /></g></svg>';
        //let status_str = feature.get('is_vacant') ? getDisplayNameFromStatus(feature.get('status')) + ' (vacant)' : getDisplayNameFromStatus(feature.get('status'))
        let a_status = getStatusForColour(
          feature,
          false,
          this.display_at_time_of_submitted,
        );
        let status_str = getDisplayNameFromStatus(a_status);
        let actions = this.get_actions(feature, this.contactLicenceHolder);
        let approval_link = this.get_approval_link(feature);
        let a_table = "";
        if (this.is_internal) {
          a_table =
            '<table class="table">' +
            "<tbody>" +
            "<tr>" +
            '<th scope="row">Holder/Applicant</th>' +
            "<td><span id=" +
            unique_id +
            "></span></td>" +
            "</tr>" +
            "<tr>" +
            '<th scope="row">Status</th>' +
            "<td>" +
            status_str +
            "</td>" +
            "</tr>" +
            "<tr>" +
            '<th scope="row">Category</th>' +
            "<td>" +
            getDisplayNameOfCategory(feature.get("site_category")) +
            "</td>" +
            "</tr>" +
            "<tr>" +
            '<th scope="row">Coordinates</th>' +
            "<td>" +
            feature["values_"]["geometry"]["flatCoordinates"] +
            "</td>" +
            "</tr>" +
            approval_link +
            "<tr>" +
            '<th scope="row">Action</th>' +
            "<td>" +
            actions +
            "</td>" +
            "</tr>" +
            "</tbody>" +
            "</table>";
        } else if (this.is_external) {
          a_table =
            '<table class="table" style="white-space: nowrap;">' +
            "<tbody>" +
            "<tr>" +
            '<th scope="row">Status</th>' +
            "<td>" +
            status_str +
            "</td>" +
            "</tr>" +
            "<tr>" +
            '<th scope="row">Action</th>' +
            "<td>" +
            actions +
            "</td>" +
            "</tr>" +
            "</table>";
        }

        let content =
          '<div style="padding: 0.25em;">' +
          '<div style="background: darkgray; color: white; text-align: center; padding: 0.5em;" class="align-middle">' +
          svg_hexa +
          " site: " +
          feature.id_ +
          "</div>" +
          a_table +
          "</div>";

        this.content_element.innerHTML = content;
        this.overlay.setPosition(coord);

        fetch("/api/apiary_site/" + feature.id_ + "/relevant_applicant_name/")
          .then(async (res) => {
            if (!res.ok) {
              return res.json().then((err) => {
                throw err;
              });
            }
            const res_json = await res.json();
            let applicant_name = res_json.relevant_applicant;
            $("#" + unique_id).text(applicant_name);
          })
          .catch((error) => {
            console.log(error);
          });
      }
    },
    showPopupForLayersJson: function (
      geojson,
      coord,
      column_names,
      display_all_columns,
      target_layer,
    ) {
      let wrapper = $("<div>"); // Add wrapper element because html() used at the end exports only the contents of the jquery object
      let caption = $(
        '<div style="text-align:center; font-weight: bold;">',
      ).text(target_layer.get("title"));
      let table = $('<table style="margin-bottom: 1em;">'); //.addClass('table')
      let tbody = $("<tbody>");
      wrapper.append(caption);
      wrapper.append(table.append(tbody));

      for (let feature of geojson.features) {
        for (let key in feature.properties) {
          if (display_all_columns || column_names.includes(key)) {
            let tr = $('<tr style="border-bottom:1px solid lightgray;">');
            let th = $('<th style="padding:0 0.5em;">').text(key);
            let td = $("<td>")
              .addClass("text-nowrap")
              .text(feature.properties[key]);
            tr.append(th);
            tr.append(td);
            tbody.append(tr);
          }
        }
        this.content_element.innerHTML += wrapper.html(); // Export contents as HTML string
        this.overlay.setPosition(coord);
      }
    },
    showPopupForLayersHTML: function (
      html_str,
      coord,
      column_names,
      display_all_columns,
    ) {
      // Generate jquery object from html_str
      let html_obj = $("<div>").html(html_str);

      // Retrieve tables as jquery object
      let tables = html_obj.find("table");

      if (!display_all_columns) {
        // Hide all columns
        tables.find("th,td").css("display", "none");

        // Make a certain column visible
        for (let i = 0; i < column_names.length; i++) {
          let index = tables
            .find("th")
            .filter(function () {
              // <th> element whoose text is exactly same as column_names[i]
              return $(this).text() === column_names[i];
            })
            .css("display", "")
            .index();

          let idx = index + 1;

          // Display <td> in the same column
          let td = tables.find("td:nth-child(" + idx + ")");
          td.css("display", "");
        }
      }

      if (tables.length) {
        this.content_element.innerHTML += html_obj.html();
        this.overlay.setPosition(coord);
      }
    },
    getDegrees: function (coords) {
      return coords[0].toFixed(6) + ", " + coords[1].toFixed(6);
    },
    removeApiarySiteById: function (apiary_site_id) {
      let feature = this.apiarySitesQuerySource.getFeatureById(apiary_site_id);
      this.apiarySitesQuerySource.removeFeature(feature);
    },
    setApiarySiteSelectedStatus: function (apiary_site_id, selected) {
      let feature = this.apiarySitesQuerySource.getFeatureById(apiary_site_id);
      let style_applied = getApiaryFeatureStyle(
        getStatusForColour(feature, false, this.display_at_time_of_submitted),
        selected,
      );
      feature.setStyle(style_applied);
    },
    displayAllFeatures: function () {
      if (this.apiarySitesQuerySource.getFeatures().length > 0) {
        let view = this.map.getView();

        let ext = this.apiarySitesQuerySource.getExtent();
        let centre = [(ext[0] + ext[2]) / 2.0, (ext[1] + ext[3]) / 2.0];
        //view.fit(ext)
        let resolution = view.getResolutionForExtent(ext);
        let z = view.getZoomForResolution(resolution) - 1;
        view.animate({ zoom: z, center: centre });
      }
    },

    // Existed methods before merging
    contactLicenceHolderClicked: function (apiary_site_id) {
      this.openOnSiteInformationModal(apiary_site_id);
    },
    contactLicenceHolder: function (e) {
      //let apiary_site_id = e.target.getAttribute("data-apiary-site-id");
      let apiary_site_id = e.target.getAttribute("data-contact-licence-holder");
      this.contactLicenceHolderClicked(apiary_site_id);
      e.stopPropagation();
    },
    contactLicenceHolderOK: function (obj) {
      fetch(
        "/api/apiary_site/" + obj.apiary_site_id + "/contact_licence_holder/",
        {
          headers: { "Content-Type": "application/json" },
          method: "POST",
          body: JSON.stringify(obj),
        },
      )
        .then(async (res) => {
          if (!res.ok) {
            return res.json().then((err) => {
              throw err;
            });
          }
          this.$refs.contact_licence_holder_modal.close();
        })
        .catch((err) => {
          console.log(err);
        });
    },
    openOnSiteInformationModal: async function (apiary_site_id) {
      this.modalBindId = uuid();

      try {
        this.$nextTick(() => {
          if (this.$refs.contact_licence_holder_modal) {
            this.$refs.contact_licence_holder_modal.apiary_site_id =
              apiary_site_id;
            this.$refs.contact_licence_holder_modal.openMe();
          }
        });
      } catch (err) {
        console.log(err);
      }
    },
    showHideApiarySites: async function () {
      let vm = this;
      vm.clearApiarySitesFromMap();
      vm.clearAjaxObjects();

      let statuses = [];
      let availabilities = [];
      for (let site_status of vm.show_hide_instructions) {
        if (!site_status.show) continue;
        if (site_status.options) {
          statuses.push(site_status.id);
          for (let option of site_status.options) {
            if (option.show) availabilities.push(option.id);
          }
        } else {
          statuses.push(site_status.id);
        }
      }

      if (statuses.length === 0) return;

      vm.all_sites_loading = true;
      vm.all_sites_ajax_obj = $.ajax(
        "/api/apiary_site/list_apiary_sites/?" +
          $.param({
            statuses: statuses.join(","),
            availabilities: availabilities.join(","),
            search_text: vm.search_text,
          }),
        {
          dataType: "json",
          success: function (re) {
            vm.addApiarySitesToMap(re);
            vm.all_sites_loading = false;
          },
          error: function (jqXhr, textStatus, errorMessage) {
            console.log(errorMessage);
            vm.all_sites_loading = false;
          },
        },
      );
    }, // END: showHideApiarySites()
  },
  mounted: function () {
    let vm = this;
    this.$nextTick(() => {
      vm.addEventListeners();
    });
    vm.initMap();
    vm.setBaseLayer("osm");
    vm.set_mode("layer");
    vm.addOptionalLayers();
    vm.displayAllFeatures();
    vm.applySelect2();
    vm.showHideApiarySites();
    vm.initAwesomplete();
  },
};
</script>

<style lang="css" scoped>
@import "../apiary/map_address_search_scoped.css";
.map-wrapper {
  position: relative;
  padding: 0;
  margin: 0;
}
#filter_search_on_map {
  position: absolute;
  top: 10px;
  left: 60px;
  z-index: 99999;
}
.basemap-button {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 400;
  -moz-box-shadow: 3px 3px 3px #777;
  -webkit-box-shadow: 3px 3px 3px #777;
  box-shadow: 3px 3px 3px #777;
  -moz-filter: brightness(1);
  -webkit-filter: brightness(1);
  filter: brightness(1);
  border: 2px white solid;
}
.basemap-button:hover,
.optional-layers-button:hover {
  cursor: pointer;
  -moz-filter: brightness(0.9);
  -webkit-filter: brightness(0.9);
  filter: brightness(0.9);
}
.basemap-button:active {
  bottom: 20px;
  right: 20px;
  -moz-box-shadow: 2px 2px 2px #555;
  -webkit-box-shadow: 2px 2px 2px #555;
  box-shadow: 2px 2px 2px #555;
  -moz-filter: brightness(0.8);
  -webkit-filter: brightness(0.8);
  filter: brightness(0.8);
}
.optional-layers-wrapper {
  position: absolute;
  top: 70px;
  left: 21px;
}
.optional-layers-button {
  position: relative;
  z-index: 400;
  background: white;
  border-radius: 2px;
  border: 3px solid rgba(5, 5, 5, 0.1);
  margin-bottom: 2px;
  cursor: pointer;
  display: block;
}
.layer_options {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 410;
  background: white;
  border-radius: 2px;
  cursor: auto;
  min-width: max-content;
  /*
        box-shadow: 3px 3px 3px #777;
        -moz-filter: brightness(1.0);
        -webkit-filter: brightness(1.0);
        */
  padding: 0.5em;
  border: 3px solid rgba(5, 5, 5, 0.1);
  margin-left: 38px;
}
.ol-popup {
  position: absolute;
  min-width: 95px;
  background-color: white;
  -webkit-filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.2));
  filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.2));
  padding: 2px;
  border-radius: 4px;
  border: 1px solid #ccc;
  bottom: 12px;
  left: -50px;
}
.ol-popup:after,
.ol-popup:before {
  top: 100%;
  border: solid transparent;
  content: " ";
  height: 0;
  width: 0;
  position: absolute;
  pointer-events: none;
}
.ol-popup:after {
  border-top-color: white;
  border-width: 10px;
  left: 48px;
  margin-left: -10px;
}
.ol-popup:before {
  border-top-color: #cccccc;
  border-width: 11px;
  left: 48px;
  margin-left: -11px;
}
.ol-popup-closer {
  text-decoration: none;
  position: absolute;
  top: 2px;
  right: 8px;
}
/* Removed: 'transform: none !important' was a workaround for OL <7 but breaks OL v10 tile rendering */
.close-icon:hover {
  filter: brightness(80%);
}
.close-icon {
  position: absolute;
  left: 1px;
  top: -11px;
  filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.2));
}
.popup-wrapper {
  padding: 0.25em;
}
.popup-content-header {
  background: darkgray;
  color: white;
}
.popup-content {
  font-size: small;
}
.table_caption {
  color: green;
}
.layer_option:hover {
  cursor: pointer;
}
.filter_search_wrapper {
  position: relative;
  z-index: 1030;
}
/*
    .table_apiary_site {
        position: relative;
        z-index: 10;
    }
    */
.button_row {
  display: flex;
  justify-content: flex-end;
}
.view_all_button {
  color: #03a9f4;
  cursor: pointer;
}
.status_filter_dropdown_wrapper {
  position: relative;
}
.status_filter_dropdown_button {
  cursor: pointer;
  width: 100%;
  position: relative;
}
.status_filter_dropdown {
  position: absolute;
  background: white;
  display: none;
  border-radius: 2px;
  min-width: max-content;
  padding: 0.5em;
  border: 3px solid rgba(5, 5, 5, 0.1);
}
.sub_option {
  margin-left: 1em;
}
.dropdown_arrow::after {
  content: "";
  width: 7px;
  height: 7px;
  border: 0px;
  border-bottom: solid 2px #909090;
  border-right: solid 2px #909090;
  -ms-transform: rotate(45deg);
  -webkit-transform: rotate(45deg);
  transform: rotate(45deg);
  position: absolute;
  top: 50%;
  right: 21px;
  margin-top: -4px;
}
/*
    .status_filter_dropdown {
        position: absolute;
        display: none;
        background: white;
        padding: 1em;
    }
    */
.select2-container {
  z-index: 100000;
}
.select2-options {
  z-index: 100000;
}
.dataTables_filter {
  display: none !important;
}
.spinner_on_map {
  position: absolute;
  top: 10%;
  left: 50%;
  z-index: 100000;
}
</style>

<style>
@import "./map_address_search.css";
</style>
