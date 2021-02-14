
#ifndef RTLSDR_EXPORT_H
#define RTLSDR_EXPORT_H

#ifdef RTLSDR_STATIC_DEFINE
#  define RTLSDR_EXPORT
#  define RTLSDR_NO_EXPORT
#else
#  ifndef RTLSDR_EXPORT
#    ifdef rtlsdr_EXPORTS
        /* We are building this library */
#      define RTLSDR_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define RTLSDR_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef RTLSDR_NO_EXPORT
#    define RTLSDR_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef RTLSDR_DEPRECATED
#  define RTLSDR_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef RTLSDR_DEPRECATED_EXPORT
#  define RTLSDR_DEPRECATED_EXPORT RTLSDR_EXPORT RTLSDR_DEPRECATED
#endif

#ifndef RTLSDR_DEPRECATED_NO_EXPORT
#  define RTLSDR_DEPRECATED_NO_EXPORT RTLSDR_NO_EXPORT RTLSDR_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef RTLSDR_NO_DEPRECATED
#    define RTLSDR_NO_DEPRECATED
#  endif
#endif

#endif /* RTLSDR_EXPORT_H */
