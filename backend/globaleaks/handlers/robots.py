# -*- coding: UTF-8
# public
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from globaleaks.handlers.base import BaseHandler


class RobotstxtHandler(BaseHandler):
    @BaseHandler.transport_security_check("unauth")
    @BaseHandler.unauthenticated
    def get(self):
        """
        Get the robots.txt
        """
        self.set_header('Content-Type', 'text/plain')

        self.write("User-agent: *\n")

        if self.tstate.memc.allow_indexing:
            site = 'https://' + self.tstate.memc.hostname
            self.write("Allow: /\n")
            self.write("Sitemap: %s/sitemap.xml" % site)
        else:
            self.write("Disallow: /")


class SitemapHandler(BaseHandler):
    @BaseHandler.transport_security_check("unauth")
    @BaseHandler.unauthenticated
    def get(self):
        """
        Get the sitemap.xml
        """
        if not self.tstate.memc.allow_indexing:
            self.set_status(404)
            return

        site = 'https://' + self.tstate.memc.hostname

        self.set_header('Content-Type', 'text/xml')

        self.write("<?xml version='1.0' encoding='UTF-8' ?>\n" +
                   "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9' xmlns:xhtml='http://www.w3.org/1999/xhtml'>\n")

        for url in ['/#/', '/#/submission']:
            self.write("  <url>\n" +
                       "    <loc>" + site + url + "</loc>\n" +
                       "    <changefreq>weekly</changefreq>\n" +
                       "    <priority>1.00</priority>\n")

            for lang in sorted(self.tstate.memc.languages_enabled):
                if lang != self.tstate.memc.default_language:
                    l = lang.lower()
                    l = l.replace('_', '-')
                    self.write("    <xhtml:link rel='alternate' hreflang='" + l + "' href='" + site + "/#/?lang=" + lang + "' />\n")

            self.write("  </url>\n")

        self.write("</urlset>")
