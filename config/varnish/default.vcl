vcl 4.0;

backend default {
    .host = "127.0.0.1";
    .port = "8081";
}

sub vcl_recv {
    if (req.url ~ "^/(admin/|contact|awin-transaction)") {
        return (pass);
    }

    if (req.http.User-Agent ~ "(?i)(ads|google|bing|msn|yandex|baidu|ro|career|seznam|)bot" ||
        req.http.User-Agent ~ "(?i)(baidu|jike|symantec|)spider" ||
        req.http.User-Agent ~ "(?i)(scanner|facebookexternalhit|crawler|admantx)"
    ) {
        set req.http.X-Bot = "bot";
    }

    unset req.http.Cookie;
}

sub vcl_backend_response {
    if (bereq.url !~ "^/(admin/|contact)") {
        unset beresp.http.set-cookie;

        if (beresp.status >= 200 && beresp.status < 400) {
            if (bereq.url ~ "^/stops/") {
                set beresp.ttl = 30s;

                if (beresp.http.Vary) {
                    set beresp.http.Vary = beresp.http.Vary + ", X-Bot";
                } else {
                    set beresp.http.Vary = "X-Bot";
                }
            } else {
                set beresp.ttl = 1h;
            }
        }

    }
}
