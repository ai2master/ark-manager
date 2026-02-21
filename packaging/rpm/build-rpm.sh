#!/bin/bash
set -e

VERSION="${1:-1.0.0}"
PACKAGE_NAME="arkmanager"

echo "Building RPM package v${VERSION}..."

# Create rpmbuild structure
mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball
TEMP_DIR=$(mktemp -d)
mkdir -p "${TEMP_DIR}/${PACKAGE_NAME}-${VERSION}"
cp -r arkmanager pyproject.toml resources LICENSE README.md "${TEMP_DIR}/${PACKAGE_NAME}-${VERSION}/"
cd "${TEMP_DIR}"
tar czf ~/rpmbuild/SOURCES/${PACKAGE_NAME}-${VERSION}.tar.gz ${PACKAGE_NAME}-${VERSION}
cd -

# Update version in spec
sed "s/^Version:.*/Version:        ${VERSION}/" packaging/rpm/arkmanager.spec > ~/rpmbuild/SPECS/arkmanager.spec

# Build
rpmbuild -ba ~/rpmbuild/SPECS/arkmanager.spec

echo "RPM package built in ~/rpmbuild/RPMS/"
rm -rf "${TEMP_DIR}"
