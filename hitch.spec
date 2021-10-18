#
# Conditional build:
%bcond_with	tests		# run tests. needs internet connection
%bcond_without	doc		# build documentation (man page)

Summary:	Network proxy that terminates TLS/SSL connections
Name:		hitch
Version:	1.7.0
Release:	1
License:	BSD
Group:		Daemons
Source0:	https://hitch-tls.org/source/%{name}-%{version}.tar.gz
# Source0-md5:	03ac590be3c75264743db1db88a352b7
Patch0:		%{name}.systemd.service.patch
Patch1:		%{name}.initrc.redhat.patch
Patch2:		%{name}-openssl-1.1.patch
Patch3:		no-Werror.patch
URL:		https://hitch-tls.org/
BuildRequires:	libev-devel >= 4
BuildRequires:	libtool
BuildRequires:	openssl
BuildRequires:	openssl-devel >= 1.0.0
BuildRequires:	pkgconfig
BuildRequires:	rpmbuild(macros) >= 1.647
%if %{with doc}
BuildRequires:	docutils
%endif
Provides:	group(hitch)
Provides:	user(hitch)
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun,postun):	systemd-units >= 38
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
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
cp -p hitch.conf.example hitch.conf
%patch0
%patch1
%patch2 -p1
%patch3 -p1

%build
CFLAGS="%{rpmcflags} -fPIE"
LDFLAGS="-pie"
%{__aclocal} -I .
%{__automake}
%{__autoconf}
%configure \
	--disable-silent-rules
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

install -d $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
cp -p hitch.conf $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install -d $RPM_BUILD_ROOT%{hitch_homedir}
install -d $RPM_BUILD_ROOT%{hitch_datadir}
install -p -D hitch.service $RPM_BUILD_ROOT%{systemdunitdir}/hitch.service
install -p -D hitch.tmpfilesd.conf $RPM_BUILD_ROOT%{systemdtmpfilesdir}/hitch.conf
install -p -D hitch.initrc.redhat $RPM_BUILD_ROOT%{_initrddir}/hitch
install -d $RPM_BUILD_ROOT%{_localstatedir}/run/hitch
touch $RPM_BUILD_ROOT%{_localstatedir}/run/hitch/hitch.pid

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 334 %{hitch_group}
%useradd -u 334 -g %{hitch_group} -s /sbin/nologin -d %{hitch_homedir} %{hitch_user}

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
if [ "$1" = "0" ]; then
	%userremove %{hitch_user}
	%groupremove %{hitch_group}
fi

%files
%defattr(644,root,root,755)
%doc README.md LICENSE CHANGES.rst hitch.conf.example
%dir %{_sysconfdir}/%{name}
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/hitch.conf
%attr(754,root,root) /etc/rc.d/init.d/hitch
%attr(755,root,root) %{_sbindir}/hitch
%if %{with doc}
%{_mandir}/man5/hitch.conf.5*
%{_mandir}/man8/hitch.8*
%endif
%{systemdunitdir}/hitch.service
%{systemdtmpfilesdir}/hitch.conf
%define	no_install_post_check_tmpfiles 1
%attr(755,hitch,hitch) %dir %{_localstatedir}/run/hitch
%attr(644,hitch,hitch) %ghost %verify(not md5 mtime size)  %{_localstatedir}/run/hitch/hitch.pid
