
#ifndef RTLSDR_STATIC_EXPORT_H
#define RTLSDR_STATIC_EXPORT_H

#ifdef RTLSDR_STATIC_STATIC_DEFINE
#  define RTLSDR_STATIC_EXPORT
#  define RTLSDR_STATIC_NO_EXPORT
#else
#  ifndef RTLSDR_STATIC_EXPORT
#    ifdef rtlsdr_static_EXPORTS
        /* We are building this library */
#      define RTLSDR_STATIC_EXPORT 
#    else
        /* We are using this library */
#      define RTLSDR_STATIC_EXPORT 
#    endif
#  endif

#  ifndef RTLSDR_STATIC_NO_EXPORT
#    define RTLSDR_STATIC_NO_EXPORT 
#  endif
#endif

#ifndef RTLSDR_STATIC_DEPRECATED
#  define RTLSDR_STATIC_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef RTLSDR_STATIC_DEPRECATED_EXPORT
#  define RTLSDR_STATIC_DEPRECATED_EXPORT RTLSDR_STATIC_EXPORT RTLSDR_STATIC_DEPRECATED
#endif

#ifndef RTLSDR_STATIC_DEPRECATED_NO_EXPORT
#  define RTLSDR_STATIC_DEPRECATED_NO_EXPORT RTLSDR_STATIC_NO_EXPORT RTLSDR_STATIC_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef RTLSDR_STATIC_NO_DEPRECATED
#    define RTLSDR_STATIC_NO_DEPRECATED
#  endif
#endif

#endif /* RTLSDR_STATIC_EXPORT_H */
