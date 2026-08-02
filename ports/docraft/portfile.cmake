vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO Cadons/Docraft
    REF ${VERSION}
    SHA512 7afaccd8d2baa9d8c064d3588b094a703584a5456150f91fcfa446a02a8254140d21268fff1cb4fd9fb046b3012622dc2e7f059a5a0c9caf140c66199e4dc5c0
    HEAD_REF main
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
    -DBUILD_TESTS=OFF
)

vcpkg_cmake_install()
vcpkg_copy_pdbs()

vcpkg_copy_tools(TOOL_NAMES docraft_tool AUTO_CLEAN)

vcpkg_cmake_config_fixup(PACKAGE_NAME docraft)

file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include")

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/LICENSE")
