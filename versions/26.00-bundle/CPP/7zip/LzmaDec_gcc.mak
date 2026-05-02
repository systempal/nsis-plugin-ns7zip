# Forwarding stub: Arc_gcc.mak includes ../../LzmaDec_gcc.mak relative to make's CWD.
# When building from versions/26.00-bundle/CPP/7zip/Bundles/Nsis7z, the CWD-relative
# ../../LzmaDec_gcc.mak resolves here. Forward to the real file in the vendor tree.
include $(VENDOR_7ZIP)/LzmaDec_gcc.mak
