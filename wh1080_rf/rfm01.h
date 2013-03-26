// Choose either  RFM01 or RFM12B
#define RFM01
//#define RFM12B

#define CMD_STATUS	0x0000
#define CMD_FREQ	0xa000

#ifdef RFM01

	#define CMD_CONFIG	0x8000
	#define CMD_RCON	0xc000
	#define CMD_WAKEUP	0xe000
	#define CMD_LOWDUTY	0xcc00
	#define CMD_LOWBATT	0xc200
	#define CMD_AFC		0xc600
	#define CMD_DFILTER	0xc420
	#define CMD_DRATE	0xc800
	#define CMD_FIFO	0xce00
	#define CMD_RSTMODE	0xda00

	#define CMD_RESET	0xff00
#endif

#ifdef RFM12B

	#define CMD_CONFIG	0x8000
	#define CMD_PM		0x8200
	#define CMD_DRATE	0xc600
	#define CMD_RCON	0x9000
	#define CMD_DFILTER	0xc228
	#define CMD_FIFO	0xca00
	#define CMD_SYNCRON	0xce00
	#define CMD_FIFO_RD	0xb000
	#define CMD_AFC		0xc400
	#define CMD_TCON	0x9800
	#define CMD_PLL		0xcc12
	#define CMD_TX_WR	0xb800
	#define CMD_WAKEUP	0xe000
	#define CMD_LOWDUTY	0xc800
	#define CMD_LOWBATT	0xc000

	#define CMD_RESET	0xfe00
#endif

#ifdef RFM01
	//CONFIG
	
	#define BAND_315                (0 << 11)   //  ...0 0... .... ....
	#define BAND_433                (1 << 11)   //  ...0 1... .... ....
	#define BAND_868                (2 << 11)   //  ...1 0... .... ....
	#define BAND_915                (3 << 11)   //  ...1 1... .... ....

//	#define BAND_433		(1 << 11)
//	#define BAND_868		(1 << 12) // Tony


	#define LOWBATT_EN		(1 << 10)
	#define WAKEUP_EN		(1 << 9)

	#define NO_CLOCK		1

	#define LOAD_CAP_8C5	(0 << 4)
	#define LOAD_CAP_9C0	(1 << 4)
	#define LOAD_CAP_9C5	(2 << 4)
	#define LOAD_CAP_10C0	(3 << 4)
	#define LOAD_CAP_10C5	(4 << 4)
	#define LOAD_CAP_11C0	(5 << 4)
	#define LOAD_CAP_11C5	(6 << 4)
	#define LOAD_CAP_12C0	(7 << 4)
	#define LOAD_CAP_12C5	(8 << 4)
	#define LOAD_CAP_13C0	(9 << 4)
	#define LOAD_CAP_13C5	(10 << 4)
	#define LOAD_CAP_14C0	(11 << 4)
	#define LOAD_CAP_14C5	(12 << 4)
	#define LOAD_CAP_15C0	(13 << 4)
	#define LOAD_CAP_15C5	(14 << 4)
	#define LOAD_CAP_16C0	(15 << 4)

	#define BW_67		(6 << 1)
	#define BW_134		(5 << 1)
	#define BW_200		(4 << 1)
	#define BW_270		(3 << 1)
	#define BW_340		(2 << 1)
	#define BW_400		(1 << 1)
	#define BW_X1		(0 << 1)
	#define BW_X2		(7 << 1)

	// RCON values
	#define VDI_DRSSI		(0 << 6)
	#define VDI_DQD			(1 << 6)
	#define VDI_CR_LOCK		(2 << 6)
	#define VDI_DRSSIDQD	(3 << 6)
	
	#define LNA_20		(3 << 4)
	#define LNA_14		(1 << 4)
	#define LNA_6		(2 << 4)
	#define LNA_0		(0 << 4)

	#define LNA_XX		(3 << 4)

	#define RSSI_103	(0 << 1)
	#define RSSI_97		(1 << 1)
	#define RSSI_91		(2 << 1)
	#define RSSI_85		(3 << 1)
	#define RSSI_79		(4 << 1)
	#define RSSI_73		(5 << 1)
	#define RSSI_X1		(6 << 1)
	#define RSSI_X2		(7 << 1)
	
	#define RX_EN		1
	
	// DFILTER values
	#define CR_AUTO			(1 << 7)
	#define	CR_LOCK_FAST	(1 << 6)
	#define	CR_LOCK_SLOW	(0 << 6)
	#define FILTER_OOK		(0 << 3)
	#define FILTER_DIGITAL	(1 << 3)
	#define FILTER_X		(2 << 3)
	#define FILTER_ANALOG	(3 << 3)
	
	#define DQD_0		0
	#define DQD_1		1
	#define DQD_2		2
	#define DQD_3		3
	#define DQD_4		4
	#define DQD_5		5
	#define DQD_6		6
	#define DQD_7		7
	
	// AFC values
	#define AFC_ON		(1 << 0)
	#define AFC_OFF		(0 << 0)
	#define AFC_OUT_ON	(1 << 1)
	#define AFC_OUT_OFF	(0 << 1)
	#define AFC_FINE	(1 << 2)
	#define AFC_STROBE	(1 << 3)

	#define AFC_RL_3	(3 << 4)
	#define AFC_RL_7	(2 << 4)
	#define AFC_RL_15	(1 << 4)
	#define AFC_RL_NONE	(0 << 4)

	#define AFC_MANUAL	(0 << 6)
	#define AFC_POWERUP	(1 << 6)
	#define AFC_VDI		(2 << 6)
	#define AFC_ALWAYS	(3 << 6)
#endif

#ifdef RFM12B
	#define P16			(1 << 10)

	#define VDI_FAST	(0 << 8)	// CR_LOCK && DRSSI && DQD
	#define VDI_MEDIUM	(1 << 8)	// CR_LOCK && (DRSSI | DQD)
	#define VDI_SLOW	(2 << 8)	// DQD
	#define VDI_ON		(3 << 8)	// Always high

	#define LNA_LOW		(3 << 3)
	#define LNA_MEDIUM	(2 << 3)
	#define LNA_HIGH	(1 << 3)
	#define LNA_MAX		(0 << 3)

	#define RSSI_103	0
	#define RSSI_97		1
	#define RSSI_91		2
	#define RSSI_85		3
	#define RSSI_79		4
	#define RSSI_73		5
	#define RSSI_X1		6
	#define RSSI_X2		7

	#define BW_67		(6 << 5)
	#define BW_134		(5 << 5)
	#define BW_200		(4 << 5)
	#define BW_270		(3 << 5)
	#define BW_340		(2 << 5)
	#define BW_400		(1 << 5)
	#define BW_X1		(0 << 5)
	#define BW_X2		(7 << 5)

	// AFC values
	#define AFC_ON		(1 << 0)
	#define AFC_OFF		(0 << 0)
	#define AFC_OUT_ON	(1 << 1)
	#define AFC_OUT_OFF	(0 << 1)
	#define AFC_FINE	(1 << 2)
	#define AFC_STROBE	(1 << 3)

	#define AFC_RL_3	(3 << 4)
	#define AFC_RL_7	(2 << 4)
	#define AFC_RL_15	(1 << 4)
	#define AFC_RL_NONE	(0 << 4)

	#define AFC_MANUAL	(0 << 6)
	#define AFC_POWERUP	(1 << 6)
	#define AFC_VDI		(2 << 6)
	#define AFC_ALWAYS	(3 << 6)
#endif




#ifdef RFM01
	#define STATUS_FFIT		(1 << 15)
	#define STATUS_FFOV		(1 << 14)
	#define STATUS_WKUP     (1 << 13)
	#define STATUS_LBD		(1 << 12)
	#define STATUS_FFEM		(1 << 11)
	#define STATUS_RSSI		(1 << 10)
	#define STATUS_DRSSI	(1 << 10)
	#define STATUS_DQD		(1 << 9)
	#define STATUS_CRL		(1 << 8)
	#define STATUS_ATGL		(1 << 7)
	#define STATUS_ASAME	(1 << 6)
	#define STATUS_OFFS6	(1 << 5)
	#define STATUS_OFFS4	(1 << 4)
	#define STATUS_OFFS3	(1 << 3)
	#define STATUS_OFFS2	(1 << 2)
	#define STATUS_OFFS1	(1 << 1)
	#define STATUS_OFFS0	(1 << 0)
	#define STATUS_OFFS		0x3f
	#define STATUS_OFFSIGN	0x20
#endif

#ifdef RFM12B
	#define STATUS_RGIT		(1 << 15)
	#define STATUS_FFIT		(1 << 15)
	#define STATUS_POR		(1 << 14)
	#define STATUS_RGUR		(1 << 13)
	#define STATUS_FFOV		(1 << 13)
	#define STATUS_WKUP     (1 << 12)
	#define STATUS_EXT      (1 << 11)
	#define STATUS_LBD		(1 << 10)
	#define STATUS_FFEM		(1 << 9)
	#define STATUS_RSSI		(1 << 8)
	#define STATUS_DRSSI	(1 << 8)
	#define STATUS_DQD		(1 << 7)
	#define STATUS_CRL		(1 << 6)
	#define STATUS_ATGL		(1 << 5)
	#define STATUS_OFFS6	(1 << 4)
	#define STATUS_OFFS3	(1 << 3)
	#define STATUS_OFFS2	(1 << 2)
	#define STATUS_OFFS1	(1 << 1)
	#define STATUS_OFFS0	(1 << 0)
	#define STATUS_OFFS		0x1f
	#define STATUS_OFFSIGN	0x10
#endif

/*
 * RSSIth = RSSIsetth + Glna, where RSSIsetth is dBm and Glna is dB
 * and is expressed as dB referenced to max G. This means that zero is the
 * highest amplification, and the negative dB scales down the RSSIsetth
 * threshold.
 */

#define L0R73	{"LNA_0,RSSI_73",LNA_0,RSSI_73}
#define L0R79	{"LNA_0,RSSI_79",LNA_0,RSSI_79}
#define L0R85	{"LNA_0,RSSI_85",LNA_0,RSSI_85}
#define L0R91	{"LNA_0,RSSI_91",LNA_0,RSSI_91}
#define L0R97	{"LNA_0,RSSI_97",LNA_0,RSSI_97}
#define L0R103	{"LNA_0,RSSI_103",LNA_0,RSSI_103}
#define L6R73	{"LNA_6,RSSI_73",LNA_6,RSSI_73}
#define L6R79	{"LNA_6,RSSI_79",LNA_6,RSSI_79}
#define L6R85	{"LNA_6,RSSI_85",LNA_6,RSSI_85}
#define L6R91	{"LNA_6,RSSI_91",LNA_6,RSSI_91}
#define L6R97	{"LNA_6,RSSI_97",LNA_6,RSSI_97}
#define L6R103	{"LNA_6,RSSI_103",LNA_6,RSSI_103}
#define L14R73	{"LNA_14,RSSI_73",LNA_14,RSSI_73}
#define L14R79	{"LNA_14,RSSI_79",LNA_14,RSSI_79}
#define L14R85	{"LNA_14,RSSI_85",LNA_14,RSSI_85}
#define L14R91	{"LNA_14,RSSI_91",LNA_14,RSSI_91}
#define L14R97	{"LNA_14,RSSI_97",LNA_14,RSSI_97}
#define L14R103	{"LNA_14,RSSI_103",LNA_14,RSSI_103}
#define L20R73	{"LNA_20,RSSI_73",LNA_20,RSSI_73}
#define L20R79	{"LNA_20,RSSI_79",LNA_20,RSSI_79}
#define L20R85	{"LNA_20,RSSI_85",LNA_20,RSSI_85}
#define L20R91	{"LNA_20,RSSI_91",LNA_20,RSSI_91}
#define L20R97	{"LNA_20,RSSI_97",LNA_20,RSSI_97}
#define L20R103	{"LNA_20,RSSI_103",LNA_20,RSSI_103}

struct RSSI {
	char *name;
	uint16_t g_lna;
	uint16_t rssi_setth;
	uint16_t cmd_config;
	uint16_t cmd_rcon;
	uint16_t flags; // bit 0: active, bit 1: not suitable
	float duty[6];
};
