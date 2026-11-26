Title: Technique Described | Nmap Network Scanning

URL Source: https://nmap.org/book/vscan-technique.html

Markdown Content:
[Download](https://nmap.org/download.html)[Reference Guide](https://nmap.org/book/man.html)[Book](https://nmap.org/book/)[Docs](https://nmap.org/docs.html)[Zenmap GUI](https://nmap.org/zenmap/)[In the Movies](https://nmap.org/movies/)
*   [Nmap Network Scanning](https://nmap.org/book/toc.html)
*   [Chapter 7.Service and Application Version Detection](https://nmap.org/book/vscan.html)
*   Technique Described

[](https://nmap.org/book/vscan-technique.html)
Nmap version scanning is actually rather straightforward. It was designed to be as simple as possible while still being scalable, fast, and accurate. The truly nitty-gritty details are best discovered by downloading and reviewing the source code, but a synopsis of the techniques used follows.

Nmap first does a port scan as per your instructions, and then passes all the `open`[](https://nmap.org/book/vscan-technique.html) or `open|filtered`[](https://nmap.org/book/vscan-technique.html) TCP and/or UDP ports to the service scanning module. Those ports are then interrogated in parallel, although a single port is described here for simplicity.

1.   Nmap checks to see if the port is one of the ports to be excluded, as specified by the `Exclude` directive in `nmap-service-probes`.[](https://nmap.org/book/vscan-technique.html) If it is, Nmap will not scan this port for reasons mentioned in [the section called “`nmap-service-probes` File Format”](https://nmap.org/book/vscan-fileformat.html "nmap-service-probes File Format").

2.   If the port is TCP, Nmap starts by connecting to it. If the connection succeeds and the port had been in the `open|filtered` state, it is changed to `open`. This is rare (for TCP) since people trying to be so stealthy that they use a TCP scan type which produces `open|filtered` ports (such as FIN scan) generally know better than to blow all of their stealth by performing version detection.

3.   Once the TCP connection is made, Nmap listens for roughly five seconds. Many common services, including most FTP, SSH, SMTP, Telnet, POP3, and IMAP servers, identify themselves in an initial welcome banner.[](https://nmap.org/book/vscan-technique.html) Nmap refers to this as the “NULL probe”[](https://nmap.org/book/vscan-technique.html) because Nmap just listens for responses without sending any probe data. If any data is received, Nmap compares it to about 3,000 NULL probe signatures in its `nmap-service-probes` file (described in [the section called “`nmap-service-probes` File Format”](https://nmap.org/book/vscan-fileformat.html "nmap-service-probes File Format")). If the service is fully identified, we are done with that port! The regular expression in signatures can includes substring matches to pick version numbers out of the response. In some cases, Nmap gets a “soft match”[](https://nmap.org/book/vscan-technique.html) on the service type, but no version info. In that case, Nmap continues but only sends probes that are known to recognize the soft-matched service type.

4.   This point is where Nmap starts for UDP probes, and TCP connections continue here if the NULL probe described above fails or soft-matches. Since the reality is that most ports are used by the service they are registered to in `nmap-services`, every probe has a list of port numbers that are considered to be most effective. For example, the probe called GetRequest that recognizes web servers (among many other services) lists 80-85, 8000-8010, and 8080-8085 among its probable ports.[](https://nmap.org/book/vscan-technique.html) Nmap sequentially (in the order they appear in the file) executes the probe(s) that match the port number being scanned.

Each probe includes a probe string[](https://nmap.org/book/vscan-technique.html) (which can be arbitrary ASCII text or \xHH escaped binary), which is sent to the port. Responses that come back are compared to a list of signature regular expressions[](https://nmap.org/book/vscan-technique.html) of the same type as discussed in the NULL probe description above. As with the NULL probe, these tests can either result in a full match (ends processing for the remote service), a soft match (limits future probes to those which match a certain service), or no match at all. The exact list of regular expressions that Nmap uses to test for a match depends on the probe fallback configuration.[](https://nmap.org/book/vscan-technique.html) For instance, the data returned from the X11Probe is very unlikely to match any regular expressions crafted for the GetRequest probe. On the other hand, it is likely that results returned from a Probe such as RTSPRequest might match a regular expression crafted for GetRequest because the two protocols being tested for are closely related. So the RTSPRequest probe has a fallback to GetRequest matches. For a more comprehensive explanation, see [the section called “Cheats and Fallbacks”](https://nmap.org/book/vscan-technique.html#vscan-cheats-and-fallbacks "Cheats and Fallbacks").

[](https://nmap.org/book/vscan-technique.html)
If any response during version detection is ever received from a UDP port which was in the `open|filtered` state, that state is changed to `open`. This makes version detection an excellent complement to UDP scan, which is forced to label all scanned UDP ports as `open|filtered` when some common firewall rules are in effect. While combining UDP scanning with version detection can take many times as long as a plain UDP scan, it is an effective and useful technique. This method is described in [the section called “Distinguishing Open from Filtered UDP Ports”](https://nmap.org/book/scan-methods-udp-scan.html#scan-methods-disambiguate "Distinguishing Open from Filtered UDP Ports").

5.   In most cases, the NULL probe or the probable port probe(s) (there is usually only one) described above match the service. Since the NULL probe shares its connection with the probable port probe, this allows service detection to be done with only one brief connection in most cases. With UDP only one packet is usually required. But should the NULL probe and probable port probe(s) fail, Nmap goes through other existing probes sequentially. In the case of TCP, Nmap must make a new connection for each probe to avoid having previous probes corrupt the results. This worst-case scenario can take a bit of time, especially since Nmap must wait about five seconds for the results from each probe because of slow network connections and otherwise slowly responding services. Fortunately, Nmap utilizes several automatic techniques to speed up scans: [](https://nmap.org/book/vscan-technique.html)

    *   Nmap makes most probes generic enough to match many services. For example, the GenericLines probe sends two blank lines (“`\r\n\r\n`”) to the service. This matches daemons of many diverse service types, including FTP, ident, POP3, UUCP, Postgres, and whois. The GetRequest probe matches even more service types. Other examples include “`help\r\n`” and generic RPC and MS SMB probes.

    *   If a service matches a `softmatch` directive, [](https://nmap.org/book/vscan-technique.html) Nmap only needs to try probes that can potentially match that service.

    *   All probes were not created equal! Some match many more services than others. Because of this, Nmap uses the rarity[](https://nmap.org/book/vscan-technique.html) metric to avoid trying probes that are extremely unlikely to match. Experienced Nmap users can force all probes to be tried regardless or limit probe attempts even further than the default by using the `--version-intensity`,[](https://nmap.org/book/vscan-technique.html)`--version-all`,[](https://nmap.org/book/vscan-technique.html) and `--version-light`[](https://nmap.org/book/vscan-technique.html) options discussed in [the section called “Probe Selection and Rarity”](https://nmap.org/book/vscan-technique.html#vscan-selection-and-rarity "Probe Selection and Rarity").

6.   One of the probes tests whether the target port is running SSL.[](https://nmap.org/book/vscan-technique.html) If so (and if OpenSSL is available), Nmap connects back via SSL and restarts the service scan to determine what is listening behind the encryption. A special directive allows different probable ports for normal and SSL tunneled[](https://nmap.org/book/vscan-technique.html) connections. For example, Nmap should start against port 443 (HTTPS) with an SSL probe. But after SSL is detected and enabled, Nmap should try the GetRequest probe against port 443 because that port usually has a web server listening behind SSL encryption.

7.   Another generic probe identifies RPC-based services.[](https://nmap.org/book/vscan-technique.html) When these are found, the Nmap RPC grinder (discussed later) is initiated to brute force the RPC program number/name and supported version numbers. Similarly, an SMB post-processor for fingerprinting Windows services is available as part of the [Chapter 9, _Nmap Scripting Engine_](https://nmap.org/book/nse.html "Chapter 9. Nmap Scripting Engine").

8.   If at least one of the probes elicits some sort of response, yet Nmap is unable to recognize the service, the response content is printed to the user in the form of a _fingerprint_.[](https://nmap.org/book/vscan-technique.html)[](https://nmap.org/book/vscan-technique.html) If users know what services are actually listening, they are encouraged to submit the fingerprint to Nmap developers for integration into Nmap, as described in [the section called “Submit Service Fingerprints”](https://nmap.org/book/vscan-community.html#vscan-submit-prints "Submit Service Fingerprints").

### Cheats and Fallbacks

[](https://nmap.org/book/vscan-technique.html)[](https://nmap.org/book/vscan-technique.html)
Even though Nmap waits a generous amount of time for services to reply, sometimes an application is slow to respond to the NULL probe. This can occur for a number of reasons, including slow reverse DNS lookups performed by some services. Because of this, Nmap can sometimes match the results from a subsequent probe to a match line designed for the NULL probe.

For example, suppose we scan port 25 (SMTP) on a server to determine what is listening. As soon as we connect, that service may conduct a bunch of DNS blacklist lookups to determine whether we should be treated as spammers and denied service. Before it finishes that, Nmap gives up waiting for a NULL probe response and sends the next probe with port 25 registered, which is “`HELP\r\n`”. When the service finally completes its anti-spam checks, it prints a greeting banner, reads the Help probe, and responds as shown in [Example 7.4](https://nmap.org/book/vscan-technique.html#ex-version-null-probe-cheat "Example 7.4. NULL probe cheat example output").

Example 7.4.NULL probe cheat example output

220 hcsw.org ESMTP Sendmail 8.12.3/8.12.3/Debian-7.1; Tue, [cut]
214-2.0.0 This is sendmail version 8.12.3
214-2.0.0 Topics:
214-2.0.0       HELO    EHLO    MAIL    RCPT    DATA
214-2.0.0       RSET    NOOP    QUIT    HELP    VRFY
214-2.0.0       EXPN    VERB    ETRN    DSN     AUTH
214-2.0.0       STARTTLS
214-2.0.0 For more info use "HELP <topic>".
214-2.0.0 To report bugs in the implementation send email to
214-2.0.0       sendmail-bugs@sendmail.org.
214-2.0.0 For local information send email to Postmaster at your site.
214 2.0.0 End of HELP info

Nmap reads this data from the socket and finds that no regular expressions from the Help probe match the data returned. This is because Nmap normally expects to receive the ESMTP banner during the NULL probe and match it there.

Because this is a relatively common scenario, Nmap “cheats” by trying to match responses to any of the NULL Probe match lines if none of the probe-specific lines match. In this case, a null match line exists which reports that the program is Sendmail, the version is 8.12.3/8.12.3/Debian-7.1, and the hostname is hcsw.org.

The NULL probe cheat is actually just a specific example of a more general Nmap feature: fallbacks. The fallback directive is described in detail in [the section called “`nmap-service-probes` File Format”](https://nmap.org/book/vscan-fileformat.html "nmap-service-probes File Format"). Essentially, any probe that is likely to encounter results that can be matched by regular expressions in other probes has a fallback directive that specifies these other probes.

For example, in some configurations of the popular Apache web server, Apache won't respond to the GetRequest (“`GET / HTTP/1.0\r\n\r\n`”) probe because no virtual host name[](https://nmap.org/book/vscan-technique.html) has been specified. Nmap is still able to correctly identify these servers because those servers usually respond to the HTTPOptions probe. That probe has a fallback to the GetRequest regular expressions, which are sufficiently general to recognize Apache's responses to the HTTPOptions probes.

### Probe Selection and Rarity

[](https://nmap.org/book/vscan-technique.html)
In determining what probes to use, Nmap considers their `rarity`. This is an indication of how likely the probe is to return useful data. If a probe has a high rarity, it is considered less common and is less likely to be tried. Nmap users can specify which probes are tried by changing the intensity level[](https://nmap.org/book/vscan-technique.html) of the version scan, as described below. The precise algorithm Nmap uses when determining which probes to use follows:

1.   For TCP, the NULL probe is always tried first.

2.   All probes that have the port being scanned listed as a probable port (see [the section called “`nmap-service-probes` File Format”](https://nmap.org/book/vscan-fileformat.html "nmap-service-probes File Format")) are tried in the order they appear in `nmap-service-probes`.

3.   All other probes that have a rarity value less than or equal to the current intensity value of the scan are tried, also in the order they appear in `nmap-service-probes`.

Once a probe is found to match, the algorithm terminates and results are reported.

Because all of Nmap's probes (other than the NULL probe) have a rarity value associated with them, it is relatively easy to control how many of them are tried when performing a version scan. Simply choose an intensity level appropriate for a scan. The higher an intensity level, the more probes will be tried. So if a very comprehensive scan is desired, a high intensity level is appropriate—even though it may take longer[](https://nmap.org/book/vscan-technique.html) than a scan conducted at a lower intensity level. Nmap's default intensity level is 7[](https://nmap.org/book/vscan-technique.html) but Nmap provides the following switches for different scanning needs:
