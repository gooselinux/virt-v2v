Name:           virt-v2v
Version:        0.6.2
Release:        4%{?dist}
Summary:        Convert a virtual machine to run on KVM

Group:          Applications/System
License:        GPLv2+ and LGPLv2+
URL:            http://git.fedoraproject.org/git/virt-v2v.git
Source0:        https://fedorahosted.org/releases/v/i/virt-v2v/%{name}-v%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# Windows dependencies
# Taken from the RHEV Tools CD
# N.B. Old tools are supported on new RHEV, but not vice-versa. Don't upgrade
# this blindly! The tool will automatically update itself.
Source1:        RHEV-Application_Provisioning_Tool_46267.exe
Source2:        rhsrvany.exe

# Backported upstream patches
# Allow absolute paths in virt-v2v.conf
Patch0:         virt-v2v-0.6.2-01-11ab38d1.patch
# Change the default location of Windows VirtIO drivers on the host
Patch1:         virt-v2v-0.6.2-02-a1c88961.patch
# Install VirtIO storage and network drivers in Windows
Patch2:         virt-v2v-0.6.2-03-c96306de.patch
# Include firstboot.bat in the virt-v2v distribution
Patch3:         virt-v2v-0.6.2-04-11d8166f.patch
# Explicitly set umask to 0022 before running
Patch4:         virt-v2v-0.6.2-05-604f1b50.patch
# Identify RHEL 6 as 'OtherLinux' to RHEV
Patch5:         virt-v2v-0.6.2-06-eb616987.patch
# driver files correctly during Windows guest conversion
Patch6:         virt-v2v-0.6.2-07-a84218c3.patch

# Unfortunately, despite really being noarch, we have to make virt-v2v arch
# dependent to avoid build failures on architectures where libguestfs isn't
# available.
ExclusiveArch:  x86_64

# Perl doesn't need debuginfo
%define debug_package %{nil}

# Build system direct requirements
BuildRequires:  gettext
BuildRequires:  perl
BuildRequires:  perl(Module::Build)
BuildRequires:  perl(ExtUtils::Manifest)
BuildRequires:  perl(Test::More)
BuildRequires:  perl(Test::Pod)
BuildRequires:  perl(Test::Pod::Coverage)
BuildRequires:  perl(Module::Find)

# Runtime perl modules also required at build time for use_ok test
BuildRequires:  perl(IO::String)
BuildRequires:  perl(Locale::TextDomain)
BuildRequires:  perl(LWP::UserAgent)
BuildRequires:  perl(Module::Pluggable)
BuildRequires:  perl(Net::HTTPS)
BuildRequires:  perl(Net::SSL)
BuildRequires:  perl(Sys::Guestfs)
BuildRequires:  perl(Sys::Guestfs::Lib)
BuildRequires:  perl(Sys::Virt)
BuildRequires:  perl(URI)
BuildRequires:  perl(XML::DOM)
BuildRequires:  perl(XML::DOM::XPath)
BuildRequires:  perl(XML::Writer)

# Need an explicit package dependency for version requires
BuildRequires:  perl-libguestfs >= 1:1.2.7
BuildRequires:  perl-hivex >= 1.2.2

Requires:  perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

# Net::SSL is loaded dynamically by Net::HTTPS in Sys::VirtV2V::Transfer::ESX.
# The dependency isn't automatically discovered.
Requires:       perl(Net::SSL)

# Need an explicit package dependency for version requires
Requires:       perl-libguestfs >= 1:1.2.0

# For GuestOS transfer image
Requires:       /usr/bin/mkisofs


%description
virt-v2v is a tool for converting virtual machines to use the KVM hypervisor.
It modifies both the virtual machine image and its associated libvirt metadata.
virt-v2v will also configure a guest to use VirtIO drivers if possible.


%prep
%setup -q -n %{name}-v%{version}

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1

%build
%{__perl} Build.PL
./Build


%install
rm -rf $RPM_BUILD_ROOT
./Build install \
    --destdir $RPM_BUILD_ROOT \
    --installdirs vendor \
    --install_path locale=%{_datadir}/locale \
    --install_path confdoc=%{_mandir}/man5

# Create lib directory, used for holding software to be installed in guests
statedir=$RPM_BUILD_ROOT%{_localstatedir}/lib/virt-v2v
mkdir -p $statedir/software

# Copy Windows dependencies into place
windir=$statedir/software/windows
mkdir -p $windir

# firstboot.bat expects the RHEV APT installer to be called rhev-apt.exe
cp %{SOURCE1} $windir/rhev-apt.exe
cp %{SOURCE2} windows/firstboot.bat $windir/

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
cp v2v/virt-v2v.conf $RPM_BUILD_ROOT%{_sysconfdir}/

# Replace @V2V_LIBVIRT_DIR@ with actual location of v2v-libvirt
sed -i 's,@V2V_LIBVIRT_DIR@,%{_libdir}/v2v-libvirt,' \
    $RPM_BUILD_ROOT%{_bindir}/virt-v2v

# Remove .packlist files.
find $RPM_BUILD_ROOT -name .packlist -exec rm {} \;

%find_lang %{name}


%check
./Build test


%clean
rm -rf $RPM_BUILD_ROOT


%files -f %{name}.lang
%defattr(-,root,root,-)

%doc TODO.txt
%doc META.yml
%doc ChangeLog
%doc COPYING COPYING.LIB

# For noarch packages: vendorlib
%{perl_vendorlib}/*

# Man pages
%{_mandir}/man1/*.1*
%{_mandir}/man3/*.3*
%{_mandir}/man5/*.5*

# Executables
%attr(0755,root,root) %{_bindir}/*

%dir %{_localstatedir}/lib/virt-v2v

%config(noreplace) %{_sysconfdir}/virt-v2v.conf
%config(noreplace) %{_localstatedir}/lib/virt-v2v/software


%changelog
* Thu Aug 19 2010 Matthew Booth <mbooth@redhat.com> - 0.6.2-4
- Fix copying of VirtIO drivers during Windows conversion (RHBZ#615981)

* Wed Aug 18 2010 Matthew Booth <mbooth@redhat.com> - 0.6.2-3
- Replace rhev-apt.exe, rhsrvany.exe and firstboot.bat (RHBZ#617635)
- Enable virt-v2v to run under a restrictive umask (RHBZ#624963)
- Identify RHEL 6 as OtherLinux when converting to RHEV (RHBZ#625041)

* Tue Aug 17 2010 Matthew Booth <mbooth@redhat.com> - 0.6.2-2
- Prevent Windows from replacing VirtIO with incorrect driver (RHBZ#615981)
- Remove bundled Windows VirtIO drivers (RHBZ#617635)
- Update License tag to reflect removal of proprietary drivers

* Tue Aug 10 2010 Matthew Booth <mbooth@redhat.com> - 0.6.2-1
- Rebase to new upstream version 0.6.2

* Fri Jul 23 2010 Richard W.M. Jones <rjones@redhat.com> - 0.6.1-2
- Update License tag to note that Windows drivers are distributed under
  a non-free Red Hat Proprietary license.
- Include license text next to the drivers *and* in the documentation
  directory.
- Remove .packlist files from Perl libdirs.

* Tue Jun 22 2010 Matthew Booth <mbooth@redhat.com> - 0.6.1-1
- Update to release 0.6.1 (RHBZ#558755)

* Wed May 19 2010 Richard W.M. Jones <rjones@redhat.com> - 0.5.4-1
- Update RHEL-6 branch to release 0.5.4, from RHEL-5-V2V (RHBZ#558755).

* Fri Jan 22 2010 Matthew Booth <mbooth@redhat.com> - 0.2.0-2
- Change arch to x86_64 to prevent building where qemu isn't available.

* Tue Sep 15 2009 Matthew Booth <mbooth@redhat.com> - 0.2.0-1
- Update to release 0.2.0

* Tue Sep  4 2009 Matthew Booth <mbooth@redhat.com> - 0.1.0-1
- Initial specfile
