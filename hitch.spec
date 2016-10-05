#
# Conditional build:
%bcond_with	tests		# run tests. needs internet connection

Summary:	Network proxy that terminates TLS/SSL connections
Name:		hitch
Version:	1.4.1
Release:	1
License:	BSD
Group:		Daemons
Source0:	https://hitch-tls.org/source/%{name}-%{version}.tar.gz
# Source0-md5:	111913964c35bb6ef41474273e0b6755
Patch0:		%{name}.systemd.service.patch
Patch1:		%{name}.initrc.redhat.patch
URL:		https://hitch-tls.org/
BuildRequires:	libev-devel >= 4
BuildRequires:	libtool
BuildRequires:	openssl
BuildRequires:	openssl-devel >= 1.0.0
BuildRequires:	rpmbuild(macros) >= 1.647
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun,postun):	systemd-units >= 38
Requires:	rc-scripts
Requires:	systemd-units >= 0.38
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		hitch_user		hitch
%define		hitch_group		hitch
%define		hitch_homedir	%{_localstatedir}/lib/hitch
%define		hitch_confdir	%{_sysconfdir}/%{name}
%define		hitch_datadir	%{_datadir}/hitch

%description
hitch is a network proxy that terminates TLS/SSL connections and
forwards the unencrypted traffic to some backend. It is designed to
handle 10s of thousands of connections efficiently on multicore
machines.

%prep
%setup -q
%patch0
%patch1

%build
CFLAGS="%{rpmcflags} -fPIE"
LDFLAGS="-pie"
CPPFLAGS="-I%{_includedir}/libev"
%configure
%{__make}

%if %{with tests}
cd src/tests
./runtests
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

%{__rm} -r $RPM_BUILD_ROOT%{_docdir}/%{name}

sed '
	s/user = ""/user = "%{hitch_user}"/g;
	s/group = ""/group = "%{hitch_group}"/g;
	s/backend = "\[127.0.0.1\]:8000"/backend = "[127.0.0.1]:6081"/g;
	s/syslog = off/syslog = on/g;
	' hitch.conf.example > hitch.conf
	sed -i 's/daemon = off/daemon = on/g;' hitch.conf

install -p -D hitch.conf $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/hitch.conf
install -d $RPM_BUILD_ROOT%{hitch_homedir}
install -d $RPM_BUILD_ROOT%{hitch_datadir}
install -p -D hitch.service $RPM_BUILD_ROOT%{systemdunitdir}/hitch.service
install -p -D hitch.tmpfilesd.conf $RPM_BUILD_ROOT%{systemdtmpfilesdir}/hitch.conf
install -p -D hitch.initrc.redhat $RPM_BUILD_ROOT%{_initrddir}/hitch
install -d $RPM_BUILD_ROOT%{_localstatedir}/run/hitch
touch $RPM_BUILD_ROOT%{_localstatedir}/run/hitch/hitch.pid

%clean
rm -rf $RPM_BUILD_ROOT

%if 0
# TODO: register uid/gid
%pre
%groupadd -r %{hitch_group}
%useradd -r -g %{hitch_group} -s /sbin/nologin -d %{hitch_homedir} %{hitch_user}
%endif

%post
%systemd_post hitch.service
%tmpfiles_create %{systemdtmpfilesdir}/hitch.conf
/sbin/chkconfig --add hitch
%service hitch restart

%preun
%systemd_preun hitch.service
%service hitch stop
/sbin/chkconfig --del hitch

%postun
%systemd_postun_with_restart hitch.service

%files
%defattr(644,root,root,755)
%doc README.md LICENSE CHANGES.rst hitch.conf.example
%dir %{_sysconfdir}/%{name}
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/hitch.conf
%attr(754,root,root) /etc/rc.d/init.d/hitch
%attr(755,root,root) %{_sbindir}/hitch
%{_mandir}/man8/hitch.8*
%{systemdunitdir}/hitch.service
%{systemdtmpfilesdir}/hitch.conf
%define	no_install_post_check_tmpfiles 1
%attr(755,hitch,hitch) %dir %{_localstatedir}/run/hitch
%attr(644,hitch,hitch) %ghost %verify(not md5 mtime size)  %{_localstatedir}/run/hitch/hitch.pid
