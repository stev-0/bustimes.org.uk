(function () {

    'use strict';

    /*jslint
        browser: true
    */
    /*global
        L, loadjs
    */
    var map = document.getElementById('map');

    if (!map || !map.clientWidth) {
        return;
    }

    function setUpMap() {
        var h1 = document.getElementsByTagName('h1')[0],
            items = document.getElementsByTagName('li'),
            i, // transient
            metaElements, // transient
            latLng, // transient
            mainLocations = [], // locations with labels
            labels = []; // label elements

        for (i = items.length - 1; i >= 0; i -= 1) {
            if (items[i].getAttribute('itemtype') === 'https://schema.org/BusStop' && items[i].className != 'OTH') {
                metaElements = items[i].getElementsByTagName('meta');
                if (metaElements.length) {
                    latLng = [
                        parseFloat(metaElements[0].getAttribute('content')),
                        parseFloat(metaElements[1].getAttribute('content'))
                    ];
                    mainLocations.push(latLng);
                    labels.push(items[i]);
                }
            }
        }

        // Add the main stop (for the stop point detail page)
        if (h1.getAttribute('itemprop') === 'name') {
            metaElements = document.getElementsByTagName('meta');
            for (i = 0; i < metaElements.length; i++) {
                if (metaElements[i].getAttribute('itemprop') === 'latitude') {
                    mainLocations.push([
                        parseFloat(metaElements[i].getAttribute('content')),
                        parseFloat(metaElements[i + 1].getAttribute('content'))
                    ]);
                    break;
                }
            }
        }

        if (mainLocations.length) {
            map = L.map('map');
            var tileURL = 'https://bustimes.org.uk/styles/klokantech-basic/{z}/{x}/{y}' + (L.Browser.retina ? '@2x' : '') + '.png',
                pin = L.icon({
                    iconUrl:    '/static/pin.svg',
                    iconSize:   [16, 22],
                    iconAnchor: [8, 22],
                }),
                pinWhite = L.icon({
                    iconUrl:    '/static/pin-white.svg',
                    iconSize:   [16, 22],
                    iconAnchor: [8, 22],
                    popupAnchor: [0, -22],
                }),
                setUpPopup = function (location, label) {
                    var marker = L.marker(location, {icon: pinWhite}).addTo(map).bindPopup(label.innerHTML),
                        a = label.getElementsByTagName('a');
                    if (a.length) {
                        a[0].onmouseover = function () {
                            marker.openPopup();
                        };
                    }
                };

            L.tileLayer(tileURL, {
                attribution: '© <a href="https://openmaptiles.org">OpenMapTiles</a> | © <a href="https://www.openstreetmap.org">OpenStreetMap contributors</a>'
            }).addTo(map);

            if (mainLocations.length > labels.length) { // on a stop point detail page
                i = mainLocations.length - 1;
                L.marker(mainLocations[i], {icon: pin}).addTo(map);
                map.setView(mainLocations[i], 17);
            } else {
                var polyline;
                if (window.geometry) {
                    polyline = L.geoJson(window.geometry, {
                        style: {
                            weight: 2
                        }
                    });
                    polyline.addTo(map);
                }
                map.fitBounds((polyline || L.polyline(mainLocations)).getBounds(), {
                    padding: [10, 20]
                });
            }

            for (i = labels.length - 1; i >= 0; i -= 1) {
                setUpPopup(mainLocations[i], labels[i], items[i]);
            }
        }
    }

    loadjs(['/static/js/bower_components/leaflet/dist/leaflet.js', '/static/js/bower_components/leaflet/dist/leaflet.css'], {
        success: setUpMap
    });

})();
